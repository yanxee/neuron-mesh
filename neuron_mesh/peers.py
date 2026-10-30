from __future__ import annotations

import asyncio
import contextlib
import hashlib
import time

import httpx

from .capabilities import CapabilityService
from .config import Settings
from .models import NodeCapability, PeerAnnouncement, PeerView
from .security import NodeIdentity, b64d
from .storage import Database, utc_now


class PeerMesh:
    def __init__(
        self,
        settings: Settings,
        database: Database,
        identity: NodeIdentity,
        capabilities: CapabilityService,
    ) -> None:
        self.settings = settings
        self.database = database
        self.identity = identity
        self.capabilities = capabilities
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._client = httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    @property
    def auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.settings.shared_token}"}

    def announcement(self, resident_state: str = "resident") -> PeerAnnouncement:
        signed = self.capabilities.signed(resident_state)
        return PeerAnnouncement.model_validate(signed)

    def register(self, announcement: PeerAnnouncement) -> PeerView:
        capability = announcement.capability
        public_raw = b64d(announcement.public_key_b64)
        expected_id = hashlib.sha256(public_raw).hexdigest()[:32]
        if expected_id != capability.node_id:
            raise ValueError("node_id does not match public key")
        if capability.node_id == self.identity.node_id:
            raise ValueError("cannot register self as a remote peer")
        if time.time() - capability.observed_at > 300:
            raise ValueError("peer capability record is stale")
        if not NodeIdentity.verify(
            announcement.public_key_b64,
            capability.model_dump(mode="json"),
            announcement.signature_b64,
        ):
            raise ValueError("invalid peer capability signature")

        now = utc_now()
        with self.database.connection() as connection:
            existing = connection.execute(
                "SELECT rtt_ms FROM peers WHERE node_id = ?", (capability.node_id,)
            ).fetchone()
            connection.execute(
                """
                INSERT INTO peers(
                    node_id, name, public_url, failure_domain,
                    public_key_b64, signature_b64, capability_json, last_seen, rtt_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(node_id) DO UPDATE SET
                    name = excluded.name,
                    public_url = excluded.public_url,
                    failure_domain = excluded.failure_domain,
                    public_key_b64 = excluded.public_key_b64,
                    signature_b64 = excluded.signature_b64,
                    capability_json = excluded.capability_json,
                    last_seen = excluded.last_seen
                """,
                (
                    capability.node_id,
                    capability.node_name,
                    capability.network.public_url,
                    capability.network.failure_domain,
                    announcement.public_key_b64,
                    announcement.signature_b64,
                    capability.model_dump_json(),
                    now,
                    existing["rtt_ms"] if existing else None,
                ),
            )
        return self._row_to_view(
            {
                "node_id": capability.node_id,
                "name": capability.node_name,
                "public_url": capability.network.public_url,
                "failure_domain": capability.network.failure_domain,
                "public_key_b64": announcement.public_key_b64,
                "signature_b64": announcement.signature_b64,
                "capability_json": capability.model_dump_json(),
                "last_seen": now,
                "rtt_ms": existing["rtt_ms"] if existing else None,
            }
        )

    def _row_to_view(self, row: object) -> PeerView:
        item = dict(row)  # type: ignore[arg-type]
        capability = NodeCapability.model_validate_json(item["capability_json"])
        return PeerView(
            node_id=item["node_id"],
            name=item["name"],
            public_url=item["public_url"],
            failure_domain=item["failure_domain"],
            capability=capability,
            public_key_b64=item["public_key_b64"],
            signature_b64=item["signature_b64"],
            last_seen=item["last_seen"],
            rtt_ms=item["rtt_ms"],
            online=True,
        )

    def list_live(self, max_age_seconds: float = 60.0) -> list[PeerView]:
        cutoff = time.time() - max_age_seconds
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM peers ORDER BY rtt_ms IS NULL, rtt_ms, name"
            ).fetchall()
        peers: list[PeerView] = []
        for row in rows:
            try:
                seen = row["last_seen"]
                from datetime import datetime

                seen_timestamp = datetime.fromisoformat(seen).timestamp()
            except (ValueError, TypeError):
                seen_timestamp = 0
            if seen_timestamp >= cutoff:
                peers.append(self._row_to_view(row))
        return peers

    def candidates(self, model_id: str) -> list[PeerView]:
        return [
            peer
            for peer in self.list_live()
            if peer.capability.admitted
            and peer.capability.resident_state not in {"draining", "hibernated"}
            if model_id in peer.capability.models
            and (
                "full-model" in peer.capability.service_roles
                or "pipeline-worker" in peer.capability.service_roles
            )
        ]

    async def choose(self, model_id: str) -> PeerView | None:
        candidates = self.candidates(model_id)
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda peer: (
                peer.rtt_ms if peer.rtt_ms is not None else 10_000,
                peer.capability.compute.ram_available_bytes * -1,
            ),
        )

    async def announce_to(self, endpoint: str, resident_state: str = "resident") -> None:
        payload = self.announcement(resident_state).model_dump(mode="json")
        url = f"{endpoint.rstrip('/')}/v1/peers/announce"
        response = await self._client.post(url, json=payload, headers=self.auth_headers)
        response.raise_for_status()

    async def _merge_peer_list(self, endpoint: str) -> None:
        url = f"{endpoint.rstrip('/')}/v1/peers"
        response = await self._client.get(url, headers=self.auth_headers)
        response.raise_for_status()
        for raw_peer in response.json():
            try:
                peer = PeerView.model_validate(raw_peer)
                if peer.node_id == self.identity.node_id:
                    continue
                self.register(
                    PeerAnnouncement(
                        capability=peer.capability,
                        public_key_b64=peer.public_key_b64,
                        signature_b64=peer.signature_b64,
                    )
                )
            except Exception:
                continue

    async def refresh_once(self) -> None:
        if self.settings.offline:
            return
        endpoints = set(self.settings.bootstrap_peers)
        endpoints.update(peer.public_url for peer in self.list_live())
        endpoints.discard(self.settings.public_url)

        for endpoint in list(endpoints):
            try:
                await self.announce_to(endpoint)
            except httpx.HTTPError:
                continue

        async def refresh_one(endpoint: str) -> None:
            try:
                started = time.perf_counter()
                await self._merge_peer_list(endpoint)
                rtt = (time.perf_counter() - started) * 1000
                with self.database.connection() as connection:
                    connection.execute(
                        "UPDATE peers SET rtt_ms = ? WHERE public_url = ?",
                        (rtt, endpoint.rstrip("/")),
                    )
            except httpx.HTTPError:
                return

        await asyncio.gather(*(refresh_one(endpoint) for endpoint in endpoints))

    async def _run(self) -> None:
        while not self._stop.is_set():
            await self.refresh_once()
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._stop.wait(), timeout=self.settings.peer_refresh_seconds
                )

    async def start(self) -> None:
        if self.settings.offline or self._task is not None:
            return
        self._task = asyncio.create_task(self._run(), name="peer-refresh")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task
            self._task = None
        await self._client.aclose()

    async def post_json(
        self, endpoint: str, path: str, payload: dict[str, object]
    ) -> dict[str, object]:
        response = await self._client.post(
            f"{endpoint.rstrip('/')}{path}",
            json=payload,
            headers=self.auth_headers,
        )
        response.raise_for_status()
        return response.json()

    async def get_json(
        self, endpoint: str, path: str
    ) -> dict[str, object]:
        response = await self._client.get(
            f"{endpoint.rstrip('/')}{path}", headers=self.auth_headers
        )
        response.raise_for_status()
        return response.json()

    async def forward_chat(
        self, endpoint: str, payload: dict[str, object]
    ) -> dict[str, object]:
        response = await self._client.post(
            f"{endpoint.rstrip('/')}/v1/chat/completions",
            json=payload,
            headers={
                **self.auth_headers,
                "X-Neuron-Forwarded": "1",
                "X-Neuron-Route": "local",
            },
        )
        response.raise_for_status()
        return response.json()

    async def delete(self, endpoint: str, path: str) -> bool:
        response = await self._client.delete(
            f"{endpoint.rstrip('/')}{path}", headers=self.auth_headers
        )
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True

