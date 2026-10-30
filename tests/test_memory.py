from pathlib import Path

from neuron_mesh.memory import MemoryStore
from neuron_mesh.models import MemoryWriteRequest
from neuron_mesh.security import MemoryCipher
from neuron_mesh.storage import Database


def make_store(tmp_path: Path) -> tuple[MemoryStore, Database]:
    database = Database(tmp_path / "test.db")
    database.initialize()
    store = MemoryStore(
        database,
        MemoryCipher(tmp_path),
        local_failure_domain="domain-a",
        hot_memory_limit_bytes=1024,
    )
    return store, database


def test_memory_is_encrypted_and_blind_searchable(tmp_path: Path) -> None:
    store, database = make_store(tmp_path)
    record = store.write(
        MemoryWriteRequest(
            namespace_id="ns-1",
            owner_id="owner-1",
            role_id="agent://researcher",
            kind="fact",
            text="量子纠错需要额外的逻辑量子比特。",
            summary="量子纠错需要冗余资源",
            importance=5,
        )
    )

    assert record.durability == "D1"
    assert record.cipher is not None
    results = store.search("ns-1", "量子纠错")
    assert [item.memory_id for item in results] == [record.memory_id]
    text, summary = store.decrypt(results[0])
    assert "逻辑量子比特" in text
    assert summary == "量子纠错需要冗余资源"

    with database.connection() as connection:
        row = connection.execute(
            "SELECT cipher FROM memories WHERE memory_id = ?", (record.memory_id,)
        ).fetchone()
        raw = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'memory_%'"
        ).fetchall()
    assert row["cipher"] != "量子纠错需要额外的逻辑量子比特。"
    assert raw


def test_tombstoned_memory_is_not_searchable(tmp_path: Path) -> None:
    store, _ = make_store(tmp_path)
    record = store.write(
        MemoryWriteRequest(
            namespace_id="ns-1",
            owner_id="owner-1",
            text="可删除的首都信息",
        )
    )
    store.set_status(record.memory_id, "tombstoned")

    assert store.search("ns-1", "首都") == []


def test_cold_record_keeps_pointer_but_not_local_cipher(tmp_path: Path) -> None:
    store, _ = make_store(tmp_path)
    record = store.write(
        MemoryWriteRequest(
            namespace_id="ns-1",
            owner_id="owner-1",
            text="一份需要转移到远端的长记忆",
        )
    )
    moved = store.mark_cold_unloaded(record.memory_id)

    assert moved is not None
    assert moved.tier == "cold"
    assert moved.cipher is None
    assert moved.content_hash == record.content_hash
    assert [item.memory_id for item in store.search("ns-1", "远端")] == [
        record.memory_id
    ]

