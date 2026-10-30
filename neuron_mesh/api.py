from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .backend import LocalBackend
from .backup import BackupManager
from .capabilities import CapabilityService
from .config import Settings
from .memory import BackupCopy, MemoryStore
from .models import (
    AvatarIntentRequest,
    BackupFetchResponse,
    BackupStoreRequest,
    ChatCompletionRequest,
    MemoryWriteRequest,
    PeerAnnouncement,
    RoleCreateRequest,
    ShutdownReceipt,
    SpatialEvent,
    SpatialSessionOpen,
)
from .peers import PeerMesh
from .roles import RoleStore
from .security import MemoryCipher, NodeIdentity, b64d, b64e, bearer_matches
from .spatial import SpatialManager
from .storage import Database, utc_now

logger = logging.getLogger("neuron_mesh")


@dataclass(slots=True)
class Runtime:
    settings: Settings
    database: Database
    identity: NodeIdentity
    memory_cipher: MemoryCipher
    capabilities: CapabilityService
    memory: MemoryStore
    peers: PeerMesh
    backups: BackupManager
    backend: LocalBackend
    roles: RoleStore
    spatial: SpatialManager
    resident_state: str = "resident"
    maintenance_task: asyncio.Task[None] | None = None


def _require_token(expected_token: str):
    async def dependency(authorization: str | None = Header(default=None)) -> None:
        if not bearer_matches(expected_token, authorization):
            raise HTTPException(status_code=401, detail="invalid bearer token")

    return dependency


def _memory_roots(records: list[Any]) -> str:
    digest = hashlib.sha256()
    for memory_id in sorted(record.memory_id for record in records):
        digest.update(memory_id.encode("ascii"))
    return f"sha256:{digest.hexdigest()}"


def create_app(settings: Settings | None = None) -> FastAPI:
    configured = settings or Settings.from_env()
    configured.ensure_data_dir()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        database = Database(configured.database_path)
        database.initialize()
        identity = NodeIdentity(configured.data_dir)
        cipher = MemoryCipher(configured.data_dir)
        capabilities = CapabilityService(configured, identity)
        memory = MemoryStore(
            database,
            cipher,
            local_failure_domain=configured.failure_domain,
            hot_memory_limit_bytes=configured.hot_memory_limit_bytes,
        )
        peers = PeerMesh(configured, database, identity, capabilities)
        backups = BackupManager(
            memory, peers, local_failure_domain=configured.failure_domain
        )
        roles = RoleStore(database, identity.node_id)
        spatial = SpatialManager(roles)
        backend = LocalBackend(configured)
        runtime = Runtime(
            settings=configured,
            database=database,
            identity=identity,
            memory_cipher=cipher,
            capabilities=capabilities,
            memory=memory,
            peers=peers,
            backups=backups,
            backend=backend,
            roles=roles,
            spatial=spatial,
        )
        app.state.runtime = runtime

        async def maintenance() -> None:
            while True:
                try:
                    await peers.refresh_once()
                    await backups.sync_due(configured.backup_interval_seconds)
                except Exception:
                    logger.exception("maintenance cycle failed")
                await asyncio.sleep(min(configured.peer_refresh_seconds, 30))

        await peers.start()
        runtime.maintenance_task = asyncio.create_task(maintenance(), name="maintenance")
        try:
            yield
        finally:
            if runtime.maintenance_task:
                runtime.maintenance_task.cancel()
                await asyncio.gather(
                    runtime.maintenance_task, return_exceptions=True
                )
            await peers.stop()
            await backend.close()

    app = FastAPI(
        title="Neuron Mesh",
        version="0.1.0",
        description="Invite-only decentralized inference and persistent memory research MVP",
        lifespan=lifespan,
    )
    if configured.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=configured.cors_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type", "X-Neuron-Route"],
        )

    auth = _require_token(configured.shared_token)

    def runtime(request: Request) -> Runtime:
        return request.app.state.runtime

    @app.get("/healthz")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/node/capabilities", dependencies=[Depends(auth)])
    async def node_capabilities(request: Request) -> dict[str, object]:
        state = runtime(request)
        return state.capabilities.signed(state.resident_state)

    @app.get("/v1/node/resources", dependencies=[Depends(auth)])
    async def node_resources(request: Request) -> dict[str, object]:
        state = runtime(request)
        return state.capabilities.current(state.resident_state).model_dump(mode="json")

    @app.get("/v1/network/status", dependencies=[Depends(auth)])
    async def network_status(request: Request) -> dict[str, object]:
        state = runtime(request)
        peers = state.peers.list_live()
        return {
            "node_id": state.identity.node_id,
            "mode": (
                "networked"
                if peers and not state.settings.offline and state.resident_state != "draining"
                else "offline-autonomous"
            ),
            "resident_state": state.resident_state,
            "online_peer_count": len(peers),
            "peers": [peer.model_dump(mode="json") for peer in peers],
        }

    @app.get("/v1/peers", dependencies=[Depends(auth)])
    async def list_peers(request: Request) -> list[dict[str, object]]:
        return [
            peer.model_dump(mode="json")
            for peer in runtime(request).peers.list_live()
        ]

    @app.post("/v1/peers/announce", dependencies=[Depends(auth)])
    async def announce_peer(payload: PeerAnnouncement, request: Request) -> dict[str, object]:
        try:
            peer = runtime(request).peers.register(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return peer.model_dump(mode="json")

    @app.post("/v1/node/drain", dependencies=[Depends(auth)])
    async def drain(request: Request) -> ShutdownReceipt:
        state = runtime(request)
        state.resident_state = "draining"
        records = state.memory.list_all_active()
        replica_count = 0
        for record in records:
            replica_count += len(await state.backups.backup_memory(record))
        root = _memory_roots(records)
        unsigned = {
            "node_id": state.identity.node_id,
            "memory_count": len(records),
            "replica_count": replica_count,
            "memory_ids_root": root,
            "created_at": utc_now(),
        }
        return ShutdownReceipt(
            **unsigned,
            signature_b64=state.identity.sign(unsigned),
        )

    @app.post("/v1/node/resume", dependencies=[Depends(auth)])
    async def resume(request: Request) -> dict[str, str]:
        state = runtime(request)
        state.resident_state = "resident"
        return {"status": "resident", "node_id": state.identity.node_id}

    @app.get("/v1/models", dependencies=[Depends(auth)])
    async def models(request: Request) -> dict[str, object]:
        state = runtime(request)
        return {
            "object": "list",
            "data": [
                {
                    "id": state.settings.model_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "neuron-mesh",
                }
            ],
        }

    @app.post("/v1/chat/completions", dependencies=[Depends(auth)])
    async def chat_completions(
        payload: ChatCompletionRequest,
        request: Request,
        route_header: str | None = Header(default=None, alias="X-Neuron-Route"),
        forwarded: str | None = Header(default=None, alias="X-Neuron-Forwarded"),
    ):
        state = runtime(request)
        route = (route_header or "auto").lower()
        if route not in {"auto", "local", "network"}:
            raise HTTPException(status_code=400, detail="invalid X-Neuron-Route")

        use_network = (
            route == "network"
            or (route == "auto" and state.settings.prefer_remote)
        ) and not state.settings.offline and forwarded != "1"
        peer = await state.peers.choose(payload.model) if use_network else None
        response: dict[str, Any]
        if peer:
            forwarded_payload = payload.model_dump(mode="json", exclude_none=True)
            forwarded_payload["stream"] = False
            try:
                response = dict(
                    await state.peers.forward_chat(peer.public_url, forwarded_payload)
                )
                response["x_neuron"] = {
                    "mode": "networked",
                    "executed_by": peer.node_id,
                }
            except httpx.HTTPError as exc:
                if route == "network":
                    raise HTTPException(
                        status_code=502, detail="selected peer failed"
                    ) from exc
                response = await state.backend.chat(payload)
                response["x_neuron"] = {
                    "mode": "offline-autonomous",
                    "executed_by": state.identity.node_id,
                }
        else:
            if route == "network":
                raise HTTPException(status_code=503, detail="no eligible peer")
            response = await state.backend.chat(payload)
            response["x_neuron"] = {
                "mode": (
                    "offline-autonomous"
                    if state.settings.offline
                    else "local"
                ),
                "executed_by": state.identity.node_id,
            }

        if payload.stream:
            return StreamingResponse(
                state.backend.stream_text(response),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        return response

    @app.post("/v1/memory/write", dependencies=[Depends(auth)])
    async def write_memory(
        payload: MemoryWriteRequest,
        request: Request,
        replicate: bool = Query(default=False),
    ) -> dict[str, object]:
        state = runtime(request)
        record = state.memory.write(payload)
        if replicate and not state.settings.offline:
            await state.backups.backup_memory(record)
            record = state.memory.get(record.memory_id) or record
        return state.memory.to_view(record).model_dump(mode="json")

    @app.get("/v1/memory/search", dependencies=[Depends(auth)])
    async def search_memory(
        request: Request,
        namespace_id: str,
        q: str,
        limit: int = Query(default=10, ge=1, le=100),
        allow_remote: bool = Query(default=True),
        include_sealed: bool = Query(default=False),
    ) -> list[dict[str, object]]:
        state = runtime(request)
        records = state.memory.search(
            namespace_id, q, limit=limit, include_sealed=include_sealed
        )
        views: list[dict[str, object]] = []
        for record in records:
            if record.cipher is None and allow_remote:
                record = await state.backups.materialize(record)
            views.append(state.memory.to_view(record).model_dump(mode="json"))
        return views

    @app.get("/v1/memory/{memory_id}", dependencies=[Depends(auth)])
    async def get_memory(
        memory_id: str,
        request: Request,
        allow_remote: bool = Query(default=True),
    ) -> dict[str, object]:
        state = runtime(request)
        record = state.memory.get(memory_id)
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        if record.cipher is None and allow_remote:
            record = await state.backups.materialize(record)
        return state.memory.to_view(record).model_dump(mode="json")

    @app.post("/v1/memory/{memory_id}/seal", dependencies=[Depends(auth)])
    async def seal_memory(memory_id: str, request: Request) -> dict[str, object]:
        state = runtime(request)
        record = state.memory.set_status(memory_id, "sealed")
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        return state.memory.to_view(record).model_dump(mode="json")

    @app.post("/v1/memory/{memory_id}/unseal", dependencies=[Depends(auth)])
    async def unseal_memory(memory_id: str, request: Request) -> dict[str, object]:
        state = runtime(request)
        record = state.memory.set_status(memory_id, "active")
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        return state.memory.to_view(record).model_dump(mode="json")

    @app.post("/v1/memory/{memory_id}/relocate", dependencies=[Depends(auth)])
    async def relocate_memory(memory_id: str, request: Request) -> dict[str, object]:
        state = runtime(request)
        record = state.memory.get(memory_id)
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        try:
            moved = await state.backups.relocate_cold(record)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return state.memory.to_view(moved).model_dump(mode="json")

    @app.delete("/v1/memory/{memory_id}", dependencies=[Depends(auth)])
    async def delete_memory(memory_id: str, request: Request) -> dict[str, object]:
        state = runtime(request)
        record = state.memory.set_status(memory_id, "tombstoned")
        if record is None:
            raise HTTPException(status_code=404, detail="memory not found")
        remote_deletions = await state.backups.propagate_delete(memory_id)
        return {
            "memory_id": memory_id,
            "status": "tombstoned",
            "remote_deletions": remote_deletions,
        }

    @app.post("/v1/memory/backup/run", dependencies=[Depends(auth)])
    async def run_backup(request: Request) -> dict[str, int]:
        state = runtime(request)
        count = await state.backups.sync_due(0)
        return {"memories_backed_up": count}

    @app.post("/v1/internal/backups", dependencies=[Depends(auth)])
    async def store_backup(payload: BackupStoreRequest, request: Request) -> dict[str, str]:
        state = runtime(request)
        cipher = b64d(payload.cipher_b64)
        nonce = b64d(payload.nonce_b64)
        if len(cipher) > state.settings.max_request_bytes:
            raise HTTPException(status_code=413, detail="backup exceeds request limit")
        state.memory.save_backup(
            BackupCopy(
                memory_id=payload.memory_id,
                namespace_id=payload.namespace_id,
                owner_id=payload.owner_id,
                content_hash=payload.content_hash,
                cipher=cipher,
                nonce=nonce,
                key_id=payload.key_id,
                size_bytes=payload.size_bytes,
                source_node_id=payload.source_node_id,
                source_failure_domain=payload.source_failure_domain,
            )
        )
        return {"status": "stored", "memory_id": payload.memory_id}

    @app.get(
        "/v1/internal/backups/{memory_id}", dependencies=[Depends(auth)]
    )
    async def fetch_backup(memory_id: str, request: Request) -> BackupFetchResponse:
        copy = runtime(request).memory.get_backup(memory_id)
        if copy is None:
            raise HTTPException(status_code=404, detail="backup not found")
        return BackupFetchResponse(
            memory_id=copy.memory_id,
            namespace_id=copy.namespace_id,
            owner_id=copy.owner_id,
            content_hash=copy.content_hash,
            cipher_b64=b64e(copy.cipher),
            nonce_b64=b64e(copy.nonce),
            key_id=copy.key_id,
            size_bytes=copy.size_bytes,
        )

    @app.delete(
        "/v1/internal/backups/{memory_id}", dependencies=[Depends(auth)]
    )
    async def delete_backup(memory_id: str, request: Request) -> dict[str, bool]:
        deleted = runtime(request).memory.delete_backup(memory_id)
        return {"deleted": deleted}

    @app.post("/v1/roles", dependencies=[Depends(auth)])
    async def create_role(payload: RoleCreateRequest, request: Request) -> dict[str, object]:
        return runtime(request).roles.create(payload).model_dump(mode="json")

    @app.get("/v1/roles/{role_id}", dependencies=[Depends(auth)])
    async def get_role(role_id: str, request: Request) -> dict[str, object]:
        role = runtime(request).roles.get(role_id)
        if role is None:
            raise HTTPException(status_code=404, detail="role not found")
        return role.model_dump(mode="json")

    @app.post("/v1/spatial/sessions", dependencies=[Depends(auth)])
    async def open_spatial_session(
        payload: SpatialSessionOpen, request: Request
    ) -> dict[str, object]:
        state = runtime(request)
        try:
            session = state.spatial.open(payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        return {
            "session_id": session.session_id,
            "role_id": session.role_id,
            "space_id": session.space_id,
            "frame_id": session.frame_id,
            "privacy_mode": session.privacy_mode,
        }

    @app.post(
        "/v1/spatial/sessions/{session_id}/events", dependencies=[Depends(auth)]
    )
    async def add_spatial_event(
        session_id: str, payload: SpatialEvent, request: Request
    ) -> dict[str, object]:
        try:
            return runtime(request).spatial.add_event(session_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.post(
        "/v1/spatial/sessions/{session_id}/intents", dependencies=[Depends(auth)]
    )
    async def submit_avatar_intent(
        session_id: str,
        payload: AvatarIntentRequest,
        request: Request,
    ) -> dict[str, object]:
        try:
            return runtime(request).spatial.submit_intent(session_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.delete(
        "/v1/spatial/sessions/{session_id}", dependencies=[Depends(auth)]
    )
    async def close_spatial_session(session_id: str, request: Request) -> dict[str, bool]:
        try:
            runtime(request).spatial.close(session_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"closed": True}

    return app


app = create_app()

