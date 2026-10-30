from __future__ import annotations

import hashlib

import httpx

from .memory import MemoryRecord, MemoryStore
from .models import BackupFetchResponse, BackupStoreRequest, PeerView
from .peers import PeerMesh
from .security import b64d, b64e


class BackupManager:
    def __init__(
        self,
        memory: MemoryStore,
        peers: PeerMesh,
        *,
        local_failure_domain: str,
        target_failure_domains: int = 3,
    ) -> None:
        self.memory = memory
        self.peers = peers
        self.local_failure_domain = local_failure_domain
        self.target_failure_domains = target_failure_domains

    def _copy_targets(self) -> list[PeerView]:
        domains: set[str] = {self.local_failure_domain}
        targets: list[PeerView] = []
        for peer in self.peers.list_live():
            domain = peer.capability.network.failure_domain
            if domain in domains:
                continue
            domains.add(domain)
            targets.append(peer)
            if len(domains) >= self.target_failure_domains:
                break
        return targets

    async def backup_memory(self, record: MemoryRecord) -> list[str]:
        if not record.cipher or not record.nonce:
            return []
        acknowledged: list[str] = []
        request = BackupStoreRequest(
            memory_id=record.memory_id,
            namespace_id=record.namespace_id,
            owner_id=record.owner_id,
            content_hash=record.content_hash,
            cipher_b64=b64e(record.cipher),
            nonce_b64=b64e(record.nonce),
            key_id=record.key_id,
            size_bytes=record.size_bytes,
            source_node_id=self.peers.identity.node_id,
            source_failure_domain=self.local_failure_domain,
            created_at=record.created_at,
        )
        payload = request.model_dump(mode="json")
        for peer in self._copy_targets():
            try:
                await self.peers.post_json(
                    peer.public_url, "/v1/internal/backups", payload
                )
                self.memory.add_replica(
                    record.memory_id,
                    peer.node_id,
                    peer.public_url,
                    peer.capability.network.failure_domain,
                )
                acknowledged.append(peer.node_id)
            except (httpx.HTTPError, ValueError):
                continue
        return acknowledged

    async def sync_due(self, interval_seconds: float) -> int:
        backed_up = 0
        for record in self.memory.due_for_backup(interval_seconds):
            if await self.backup_memory(record):
                backed_up += 1
        return backed_up

    async def materialize(self, record: MemoryRecord) -> MemoryRecord:
        if record.cipher is not None:
            return record
        for _, endpoint, _ in self.memory.replica_endpoints(record.memory_id):
            try:
                raw = await self.peers.get_json(
                    endpoint, f"/v1/internal/backups/{record.memory_id}"
                )
                fetched = BackupFetchResponse.model_validate(raw)
                cipher = b64d(fetched.cipher_b64)
                nonce = b64d(fetched.nonce_b64)
                plaintext = self.memory.cipher.open(
                    cipher, nonce, record.memory_id
                )
                if hashlib.sha256(plaintext).hexdigest() != record.content_hash:
                    continue
                restored = self.memory.restore_local(
                    record.memory_id, cipher, nonce, fetched.key_id
                )
                if restored is not None:
                    return restored
            except (httpx.HTTPError, ValueError, KeyError):
                continue
        return record

    async def relocate_cold(self, record: MemoryRecord) -> MemoryRecord:
        if not record.cipher:
            return record
        acknowledged = await self.backup_memory(record)
        remote_domains = {
            endpoint[2]
            for endpoint in self.memory.replica_endpoints(record.memory_id)
            if endpoint[2] != self.local_failure_domain
        }
        if len(remote_domains) < 1 or len(acknowledged) < 1:
            raise ValueError("refusing to evict without a remote replica acknowledgement")
        refreshed = self.memory.get(record.memory_id)
        if refreshed is None:
            raise ValueError("memory record not found")
        unloaded = self.memory.mark_cold_unloaded(record.memory_id)
        if unloaded is None:
            raise ValueError("memory record not found after relocation")
        return unloaded

    async def propagate_delete(self, memory_id: str) -> int:
        deleted = 0
        for _, endpoint, _ in self.memory.replica_endpoints(memory_id):
            try:
                if await self.peers.delete(
                    endpoint, f"/v1/internal/backups/{memory_id}"
                ):
                    deleted += 1
            except httpx.HTTPError:
                continue
        return deleted

