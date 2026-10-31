from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse

from .activity import ActivityBus
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
    RoleMigrationImport,
    RoleMigrationPackage,
    RoleMigrationRequest,
    RoleMigrationResult,
    ShutdownReceipt,
    SpatialEvent,
    SpatialSessionOpen,
)
from .peers import PeerMesh
from .roles import RoleMigrationService, RoleStore
from .security import MemoryCipher, NodeIdentity, b64d, b64e, bearer_matches
from .spatial import SpatialManager
from .storage import Database, utc_now

logger = logging.getLogger("neuron_mesh")
GRAPH_HTML_PATH = Path(__file__).with_name("graph.html")


def _node_graph_id(node_id: str) -> str:
    return f"node:{node_id}"


def _role_graph_id(role_id: str) -> str:
    return f"role:{role_id}"


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
    migrations: RoleMigrationService
    spatial: SpatialManager
    activity: ActivityBus
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


async def _drain_runtime(state: Runtime) -> ShutdownReceipt:
    state.resident_state = "draining"
    records = state.memory.list_all_active()
    replica_count = 0
    replicated_memory_count = 0
    for record in records:
        replica_count += len(await state.backups.backup_memory(record))
        refreshed = state.memory.get(record.memory_id)
        if refreshed and refreshed.durability in {"D2", "D3"}:
            replicated_memory_count += 1
    state.database.checkpoint()
    root = _memory_roots(records)
    degraded_memory_count = len(records) - replicated_memory_count
    status = (
        "local_only"
        if records and replicated_memory_count == 0
        else "degraded"
        if degraded_memory_count
        else "hardened"
    )
    unsigned = {
        "node_id": state.identity.node_id,
        "memory_count": len(records),
        "replicated_memory_count": replicated_memory_count,
        "degraded_memory_count": degraded_memory_count,
        "replica_count": replica_count,
        "memory_ids_root": root,
        "status": status,
        "created_at": utc_now(),
    }
    return ShutdownReceipt(
        **unsigned,
        signature_b64=state.identity.sign(unsigned),
    )


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
        migrations = RoleMigrationService(
            roles, memory, node_id=identity.node_id
        )
        spatial = SpatialManager(roles)
        activity = ActivityBus()
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
            migrations=migrations,
            spatial=spatial,
            activity=activity,
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
            if runtime.resident_state != "draining":
                try:
                    receipt = await asyncio.wait_for(_drain_runtime(runtime), timeout=15)
                    logger.info(
                        "automatic drain completed status=%s memories=%s replicas=%s",
                        receipt.status,
                        receipt.memory_count,
                        receipt.replica_count,
                    )
                except Exception:
                    logger.exception("automatic drain failed")
            await peers.stop()
            await backend.close()

    app = FastAPI(
        title="Neuron Mesh",
        version="0.2.0",
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

    @app.get("/readyz")
    async def ready(request: Request) -> dict[str, object]:
        state = runtime(request)
        capability = state.capabilities.current(state.resident_state)
        ready_now = capability.admitted and state.resident_state not in {
            "draining",
            "hibernated",
        }
        if not ready_now:
            raise HTTPException(
                status_code=503,
                detail={
                    "ready": False,
                    "state": capability.resident_state,
                    "reasons": capability.admission_reasons,
                },
            )
        return {"ready": True, "state": capability.resident_state}

    @app.get("/graph", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/graph/", response_class=HTMLResponse, include_in_schema=False)
    async def graph_page() -> HTMLResponse:
        return HTMLResponse(
            GRAPH_HTML_PATH.read_text(encoding="utf-8"),
            headers={
                "Cache-Control": "no-store",
                "Content-Security-Policy": (
                    "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                    "connect-src 'self'; base-uri 'none'; frame-ancestors 'none'"
                ),
                "Referrer-Policy": "no-referrer",
                "X-Content-Type-Options": "nosniff",
            },
        )

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
                if peers
                and state.capabilities.current(state.resident_state).admitted
                and not state.settings.offline
                and state.resident_state != "draining"
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
        state = runtime(request)
        try:
            peer = state.peers.register(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        state.activity.record(
            _node_graph_id(peer.node_id),
            _node_graph_id(state.identity.node_id),
            "discovery",
            detail=peer.name,
        )
        return peer.model_dump(mode="json")

    @app.get("/v1/observability/graph", dependencies=[Depends(auth)])
    async def observability_graph(request: Request) -> dict[str, object]:
        state = runtime(request)
        local_capability = state.capabilities.current(state.resident_state)
        peers = state.peers.list_live()
        nodes: list[dict[str, object]] = [
            {
                "id": _node_graph_id(state.identity.node_id),
                "kind": "host",
                "label": local_capability.node_name,
                "node_id": state.identity.node_id,
                "is_local": True,
                "online": True,
                "device_class": local_capability.device_class,
                "unit_scope": local_capability.unit_scope,
                "capacity_tier": (
                    local_capability.derived_capacity[0].tier
                    if local_capability.derived_capacity
                    else "unknown"
                ),
                "resident_state": state.resident_state,
                "service_roles": local_capability.service_roles,
                "rtt_ms": None,
            }
        ]
        edges: list[dict[str, object]] = []
        for peer in peers:
            nodes.append(
                {
                    "id": _node_graph_id(peer.node_id),
                    "kind": "host",
                    "label": peer.name,
                    "node_id": peer.node_id,
                    "is_local": False,
                    "online": peer.online,
                    "device_class": peer.capability.device_class,
                    "unit_scope": peer.capability.unit_scope,
                    "capacity_tier": (
                        peer.capability.derived_capacity[0].tier
                        if peer.capability.derived_capacity
                        else "unknown"
                    ),
                    "resident_state": peer.capability.resident_state,
                    "service_roles": peer.capability.service_roles,
                    "rtt_ms": peer.rtt_ms,
                }
            )
            edges.append(
                {
                    "id": f"peer:{state.identity.node_id}:{peer.node_id}",
                    "source": _node_graph_id(state.identity.node_id),
                    "target": _node_graph_id(peer.node_id),
                    "kind": "peer",
                    "online": peer.online,
                    "rtt_ms": peer.rtt_ms,
                }
            )

        role_summaries: list[tuple[str, dict[str, object]]] = [
            (state.identity.node_id, item) for item in state.roles.summaries()
        ]

        async def remote_roles(peer: Any) -> list[tuple[str, dict[str, object]]]:
            try:
                items = await state.peers.get_list(
                    peer.public_url,
                    "/v1/roles/summary",
                    timeout=min(2.0, configured.request_timeout_seconds),
                )
                return [(peer.node_id, item) for item in items]
            except (httpx.HTTPError, OSError, ValueError):
                return []

        if peers:
            remote_roles_by_node = await asyncio.gather(
                *(remote_roles(peer) for peer in peers)
            )
            for group in remote_roles_by_node:
                role_summaries.extend(group)

        roles_by_id: dict[str, dict[str, object]] = {}
        role_hosts: dict[str, set[str]] = {}
        for source_node_id, summary in role_summaries:
            role_id = str(summary["role_id"])
            primary_host_id = str(summary.get("primary_host_id") or source_node_id)
            hosts = role_hosts.setdefault(role_id, set())
            hosts.add(primary_host_id)
            existing = roles_by_id.get(role_id)
            if existing is None:
                roles_by_id[role_id] = {
                    "id": _role_graph_id(role_id),
                    "kind": "role",
                    "label": str(summary.get("display_name") or role_id),
                    "role_id": role_id,
                    "status": str(summary.get("status", "active")),
                    "hosts": [],
                }
            elif summary.get("status") == "migrating":
                roles_by_id[role_id]["status"] = "migrating"

        for role_id, role in roles_by_id.items():
            host_ids = sorted(role_hosts[role_id])
            role["hosts"] = [_node_graph_id(host_id) for host_id in host_ids]
            nodes.append(role)
            for host_id in host_ids:
                edges.append(
                    {
                        "id": f"hosts:{host_id}:{role_id}",
                        "source": _node_graph_id(host_id),
                        "target": _role_graph_id(role_id),
                        "kind": "hosts",
                        "online": host_id
                        in {
                            state.identity.node_id,
                            *(peer.node_id for peer in peers),
                        },
                        "rtt_ms": None,
                    }
                )

        activity = state.activity.snapshot(max_age_seconds=20)
        return {
            "server_time": time.time(),
            "mode": (
                "networked"
                if peers and not configured.offline
                else "offline-autonomous"
            ),
            "summary": {
                "hosts": len(nodes) - len(roles_by_id),
                "roles": len(roles_by_id),
                "live_edges": sum(1 for edge in edges if edge["online"]),
                "recent_activity": len(activity),
            },
            "nodes": nodes,
            "edges": edges,
            "activity": activity,
        }

    @app.post("/v1/node/drain", dependencies=[Depends(auth)])
    async def drain(request: Request) -> ShutdownReceipt:
        return await _drain_runtime(runtime(request))

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
        source_node_id: str | None = Header(
            default=None, alias="X-Neuron-Source-Node"
        ),
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
                state.activity.record(
                    _node_graph_id(state.identity.node_id),
                    _node_graph_id(peer.node_id),
                    "compute",
                    detail=payload.model,
                )
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

        known_peer_ids = {peer.node_id for peer in state.peers.list_live()}
        if forwarded == "1" and source_node_id in known_peer_ids:
            state.activity.record(
                _node_graph_id(source_node_id),
                _node_graph_id(state.identity.node_id),
                "compute",
                detail=payload.model,
            )

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
        if payload.role_id:
            state.activity.record(
                _role_graph_id(payload.role_id),
                _node_graph_id(state.identity.node_id),
                "role",
                detail="memory-write",
            )
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
        capability = state.capabilities.current(state.resident_state)
        if not capability.admitted:
            raise HTTPException(
                status_code=507,
                detail="node has not met its minimum storage admission pledge",
            )
        existing_size = state.memory.backup_size(payload.memory_id)
        current_size = state.memory.backup_usage_bytes()
        effective_quota = min(
            state.settings.storage_max_bytes,
            capability.resource_pledge.storage_min_bytes,
        )
        if current_size - existing_size + len(cipher) > effective_quota:
            raise HTTPException(
                status_code=507,
                detail="node storage pledge would be exceeded",
            )
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
        known_peer_ids = {peer.node_id for peer in state.peers.list_live()}
        if payload.source_node_id in known_peer_ids:
            state.activity.record(
                _node_graph_id(payload.source_node_id),
                _node_graph_id(state.identity.node_id),
                "storage",
                detail=payload.memory_id,
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
        state = runtime(request)
        role = state.roles.create(payload)
        state.activity.record(
            _role_graph_id(role.role_id),
            _node_graph_id(state.identity.node_id),
            "role",
            detail="created",
        )
        return role.model_dump(mode="json")

    @app.get("/v1/roles/summary", dependencies=[Depends(auth)])
    async def role_summaries(request: Request) -> list[dict[str, object]]:
        return runtime(request).roles.summaries()

    @app.post("/v1/roles/import", dependencies=[Depends(auth)])
    async def import_role(
        payload: RoleMigrationImport, request: Request
    ) -> RoleMigrationResult:
        state = runtime(request)
        try:
            role, imported, source_node_id = state.migrations.import_package(
                payload.package.model_dump(mode="json"), payload.transfer_secret
            )
        except (ValueError, KeyError, TypeError) as exc:
            raise HTTPException(status_code=400, detail="invalid migration package") from exc
        return RoleMigrationResult(
            role=role,
            imported_memory_count=imported,
            source_node_id=source_node_id,
            target_node_id=state.identity.node_id,
        )

    @app.post("/v1/roles/{role_id:path}/export", dependencies=[Depends(auth)])
    async def export_role(
        role_id: str,
        payload: RoleMigrationRequest,
        request: Request,
    ) -> RoleMigrationPackage:
        try:
            package = runtime(request).migrations.export_package(
                role_id, payload.target_node_id, payload.transfer_secret
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return RoleMigrationPackage.model_validate(package)

    @app.get("/v1/roles/{role_id:path}", dependencies=[Depends(auth)])
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
            state = runtime(request)
            result = state.spatial.submit_intent(session_id, payload)
            if result.get("accepted"):
                state.activity.record(
                    _role_graph_id(str(result["role_id"])),
                    _node_graph_id(state.identity.node_id),
                    "role",
                    detail=str(result["action"]),
                )
            return result
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

