from __future__ import annotations

import base64
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
from fastapi.testclient import TestClient

from neuron_mesh.api import create_app
from neuron_mesh.backup import BackupManager
from neuron_mesh.config import Settings
from neuron_mesh.memory import MemoryStore
from neuron_mesh.models import MemoryWriteRequest
from neuron_mesh.security import MemoryCipher
from neuron_mesh.storage import Database


def make_client(tmp_path: Path, quota_bytes: int = 5) -> TestClient:
    settings = Settings(
        node_name="storage-quota-test",
        data_dir=tmp_path,
        public_url="http://127.0.0.1:9999",
        shared_token="secret",
        offline=True,
        failure_domain="test-domain",
        storage_pledge_bytes=quota_bytes,
        storage_max_bytes=quota_bytes,
        storage_safety_reserve_bytes=0,
    )
    return TestClient(create_app(settings))


def backup_payload(memory_id: str, cipher: bytes) -> dict[str, object]:
    return {
        "memory_id": memory_id,
        "namespace_id": "ns-quota",
        "owner_id": "owner-quota",
        "content_hash": f"hash-{memory_id}",
        "cipher_b64": base64.b64encode(cipher).decode("ascii"),
        "nonce_b64": base64.b64encode(b"nonce").decode("ascii"),
        "key_id": "test-key",
        "size_bytes": len(cipher),
        "source_node_id": "source-node",
        "source_failure_domain": "source-domain",
        "created_at": "2026-01-01T00:00:00+00:00",
    }


@pytest.mark.parametrize(
    ("original_size", "replacement_size"),
    [(3, 5), (4, 2)],
    ids=["larger-replacement-at-quota", "smaller-replacement"],
)
def test_backup_replacement_excludes_previous_copy_from_quota(
    tmp_path: Path, original_size: int, replacement_size: int
) -> None:
    headers = {"Authorization": "Bearer secret"}
    with make_client(tmp_path) as client:
        original = client.post(
            "/v1/internal/backups",
            headers=headers,
            json=backup_payload("memory-1", b"a" * original_size),
        )
        assert original.status_code == 200

        replacement = client.post(
            "/v1/internal/backups",
            headers=headers,
            json=backup_payload("memory-1", b"b" * replacement_size),
        )

        assert replacement.status_code == 200
        assert replacement.json() == {"status": "stored", "memory_id": "memory-1"}
        stored = client.get("/v1/internal/backups/memory-1", headers=headers)
        assert stored.status_code == 200
        assert stored.json()["cipher_b64"] == backup_payload(
            "memory-1", b"b" * replacement_size
        )["cipher_b64"]

        runtime = client.app.state.runtime
        assert runtime.memory.backup_usage_bytes() == replacement_size


def test_backup_replacement_rejects_over_quota_and_preserves_previous_copy(
    tmp_path: Path,
) -> None:
    headers = {"Authorization": "Bearer secret"}
    with make_client(tmp_path) as client:
        original = client.post(
            "/v1/internal/backups",
            headers=headers,
            json=backup_payload("memory-1", b"a" * 4),
        )
        assert original.status_code == 200

        rejected = client.post(
            "/v1/internal/backups",
            headers=headers,
            json=backup_payload("memory-1", b"b" * 6),
        )

        assert rejected.status_code == 507
        assert rejected.json()["detail"] == "node storage pledge would be exceeded"
        stored = client.get("/v1/internal/backups/memory-1", headers=headers)
        assert stored.status_code == 200
        assert stored.json()["cipher_b64"] == backup_payload(
            "memory-1", b"a" * 4
        )["cipher_b64"]
        assert client.app.state.runtime.memory.backup_usage_bytes() == 4


def test_new_backup_exactly_at_quota_is_accepted(tmp_path: Path) -> None:
    headers = {"Authorization": "Bearer secret"}
    with make_client(tmp_path) as client:
        response = client.post(
            "/v1/internal/backups",
            headers=headers,
            json=backup_payload("memory-1", b"x" * 5),
        )

        assert response.status_code == 200
        assert client.app.state.runtime.memory.backup_usage_bytes() == 5


@pytest.mark.asyncio
async def test_rejected_backup_is_not_acknowledged_as_replica(tmp_path: Path) -> None:
    database = Database(tmp_path / "node.db")
    database.initialize()
    memory = MemoryStore(
        database,
        MemoryCipher(tmp_path),
        local_failure_domain="local-domain",
        hot_memory_limit_bytes=1024,
    )
    record = memory.write(
        MemoryWriteRequest(
            namespace_id="ns-quota",
            owner_id="owner-quota",
            text="replication must not be acknowledged on rejection",
        )
    )
    peer = SimpleNamespace(
        node_id="peer-node",
        public_url="http://peer.test",
        capability=SimpleNamespace(
            network=SimpleNamespace(failure_domain="remote-domain")
        ),
    )

    class RejectingPeers:
        identity = SimpleNamespace(node_id="source-node")

        async def post_json(self, *_args: object, **_kwargs: object) -> None:
            request = httpx.Request("POST", "http://peer.test/v1/internal/backups")
            response = httpx.Response(507, request=request)
            raise httpx.HTTPStatusError(
                "storage quota exceeded", request=request, response=response
            )

    peers = RejectingPeers()
    backups = BackupManager(
        memory, peers, local_failure_domain="local-domain"
    )
    backups._copy_targets = lambda: [peer]

    acknowledged = await backups.backup_memory(record)

    assert acknowledged == []
    refreshed = memory.get(record.memory_id)
    assert refreshed is not None
    assert refreshed.replicas == []
    assert refreshed.durability == "D1"
