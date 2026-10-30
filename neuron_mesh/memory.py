from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .models import MemoryView, MemoryWriteRequest
from .security import MemoryCipher
from .storage import Database, utc_now


@dataclass(slots=True)
class MemoryRecord:
    memory_id: str
    namespace_id: str
    owner_id: str
    role_id: str | None
    kind: str
    cipher: bytes | None
    nonce: bytes | None
    key_id: str
    content_hash: str
    size_bytes: int
    importance: int
    status: str
    tier: str
    version: int
    source_refs: list[str]
    created_at: str
    updated_at: str
    durability: str
    replicas: list[str]


@dataclass(slots=True)
class BackupCopy:
    memory_id: str
    namespace_id: str
    owner_id: str
    content_hash: str
    cipher: bytes
    nonce: bytes
    key_id: str
    size_bytes: int
    source_node_id: str
    source_failure_domain: str


class MemoryStore:
    def __init__(
        self,
        database: Database,
        cipher: MemoryCipher,
        *,
        local_failure_domain: str,
        hot_memory_limit_bytes: int,
    ) -> None:
        self.database = database
        self.cipher = cipher
        self.local_failure_domain = local_failure_domain
        self.hot_memory_limit_bytes = hot_memory_limit_bytes

    @staticmethod
    def _memory_id(namespace_id: str, content_hash: str) -> str:
        material = f"{namespace_id}\0{content_hash}".encode()
        return hashlib.sha256(material).hexdigest()

    @staticmethod
    def _payload(text: str, summary: str) -> bytes:
        return json.dumps(
            {"text": text, "summary": summary},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    def write(self, request: MemoryWriteRequest) -> MemoryRecord:
        payload = self._payload(request.text, request.summary)
        content_hash = hashlib.sha256(payload).hexdigest()
        memory_id = self._memory_id(request.namespace_id, content_hash)
        cipher, nonce = self.cipher.seal(payload, memory_id)
        terms = self.cipher.tokenize(f"{request.text}\n{request.summary}")
        now = utc_now()

        with self.database.connection() as connection:
            existing = connection.execute(
                "SELECT version FROM memories WHERE memory_id = ?", (memory_id,)
            ).fetchone()
            version = int(existing["version"]) + 1 if existing else 1
            connection.execute(
                """
                INSERT INTO memories (
                    memory_id, namespace_id, owner_id, role_id, kind,
                    cipher, nonce, key_id, content_hash, size_bytes,
                    importance, status, tier, version, source_refs,
                    created_at, updated_at, durability
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, ?, ?, ?, ?, 'D1')
                ON CONFLICT(memory_id) DO UPDATE SET
                    cipher = excluded.cipher,
                    nonce = excluded.nonce,
                    key_id = excluded.key_id,
                    size_bytes = excluded.size_bytes,
                    importance = excluded.importance,
                    status = 'active',
                    tier = excluded.tier,
                    version = excluded.version,
                    source_refs = excluded.source_refs,
                    updated_at = excluded.updated_at
                """,
                (
                    memory_id,
                    request.namespace_id,
                    request.owner_id,
                    request.role_id,
                    request.kind,
                    cipher,
                    nonce,
                    self.cipher.key_id,
                    content_hash,
                    len(payload),
                    request.importance,
                    "cold" if len(payload) > self.hot_memory_limit_bytes else "hot",
                    version,
                    json.dumps(request.source_refs, ensure_ascii=False),
                    now,
                    now,
                ),
            )
            connection.execute(
                "DELETE FROM memory_terms WHERE memory_id = ?", (memory_id,)
            )
            connection.executemany(
                "INSERT OR IGNORE INTO memory_terms(memory_id, term_hash) VALUES (?, ?)",
                [(memory_id, term) for term in terms],
            )
        record = self.get(memory_id)
        if record is None:
            raise RuntimeError("memory disappeared immediately after write")
        return record

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        with self.database.connection() as connection:
            replica_rows = connection.execute(
                """
                SELECT node_id FROM memory_replicas
                WHERE memory_id = ? ORDER BY node_id
                """,
                (row["memory_id"],),
            ).fetchall()
        return MemoryRecord(
            memory_id=row["memory_id"],
            namespace_id=row["namespace_id"],
            owner_id=row["owner_id"],
            role_id=row["role_id"],
            kind=row["kind"],
            cipher=row["cipher"],
            nonce=row["nonce"],
            key_id=row["key_id"],
            content_hash=row["content_hash"],
            size_bytes=row["size_bytes"],
            importance=row["importance"],
            status=row["status"],
            tier=row["tier"],
            version=row["version"],
            source_refs=json.loads(row["source_refs"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            durability=row["durability"],
            replicas=[item["node_id"] for item in replica_rows],
        )

    def get(self, memory_id: str) -> MemoryRecord | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM memories WHERE memory_id = ?", (memory_id,)
            ).fetchone()
        return self._row_to_record(row) if row else None

    def search(
        self, namespace_id: str, query: str, *, limit: int = 10, include_sealed: bool = False
    ) -> list[MemoryRecord]:
        allowed_statuses = ("active", "sealed") if include_sealed else ("active",)
        placeholders = ",".join("?" for _ in allowed_statuses)
        terms = sorted(self.cipher.tokenize(query))
        with self.database.connection() as connection:
            if terms:
                term_placeholders = ",".join("?" for _ in terms)
                rows = connection.execute(
                    f"""
                    SELECT m.*, COUNT(t.term_hash) AS match_score
                    FROM memories m
                    JOIN memory_terms t ON t.memory_id = m.memory_id
                    WHERE m.namespace_id = ?
                      AND m.status IN ({placeholders})
                      AND t.term_hash IN ({term_placeholders})
                    GROUP BY m.memory_id
                    ORDER BY match_score DESC, m.importance DESC, m.updated_at DESC
                    LIMIT ?
                    """,
                    (namespace_id, *allowed_statuses, *terms, limit),
                ).fetchall()
            else:
                rows = connection.execute(
                    f"""
                    SELECT * FROM memories
                    WHERE namespace_id = ? AND status IN ({placeholders})
                    ORDER BY importance DESC, updated_at DESC
                    LIMIT ?
                    """,
                    (namespace_id, *allowed_statuses, limit),
                ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def decrypt(self, record: MemoryRecord) -> tuple[str | None, str | None]:
        if not record.cipher or not record.nonce:
            return None, None
        plaintext = self.cipher.open(record.cipher, record.nonce, record.memory_id)
        payload = json.loads(plaintext)
        return payload["text"], payload.get("summary", "")

    def to_view(self, record: MemoryRecord) -> MemoryView:
        text, summary = self.decrypt(record)
        return MemoryView(
            memory_id=record.memory_id,
            namespace_id=record.namespace_id,
            owner_id=record.owner_id,
            role_id=record.role_id,
            kind=record.kind,
            text=text,
            summary=summary,
            content_hash=record.content_hash,
            source_refs=record.source_refs,
            importance=record.importance,
            status=record.status,
            tier=record.tier,
            version=record.version,
            size_bytes=record.size_bytes,
            created_at=record.created_at,
            updated_at=record.updated_at,
            durability=record.durability,
            replicas=record.replicas,
            local_content=record.cipher is not None,
        )

    def set_status(self, memory_id: str, status: str) -> MemoryRecord | None:
        with self.database.connection() as connection:
            connection.execute(
                "UPDATE memories SET status = ?, updated_at = ? WHERE memory_id = ?",
                (status, utc_now(), memory_id),
            )
        return self.get(memory_id)

    def add_replica(
        self,
        memory_id: str,
        node_id: str,
        endpoint: str,
        failure_domain: str,
    ) -> None:
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO memory_replicas(
                    memory_id, node_id, endpoint, failure_domain, acked_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(memory_id, node_id) DO UPDATE SET
                    endpoint = excluded.endpoint,
                    failure_domain = excluded.failure_domain,
                    acked_at = excluded.acked_at
                """,
                (memory_id, node_id, endpoint.rstrip("/"), failure_domain, utc_now()),
            )
            rows = connection.execute(
                "SELECT DISTINCT failure_domain FROM memory_replicas WHERE memory_id = ?",
                (memory_id,),
            ).fetchall()
            remote_domains = {
                row["failure_domain"]
                for row in rows
                if row["failure_domain"] != self.local_failure_domain
            }
            durability = "D3" if len(remote_domains) >= 2 else "D2" if remote_domains else "D1"
            connection.execute(
                "UPDATE memories SET durability = ?, updated_at = ? WHERE memory_id = ?",
                (durability, utc_now(), memory_id),
            )

    def mark_cold_unloaded(self, memory_id: str) -> MemoryRecord | None:
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE memories
                SET cipher = NULL, nonce = NULL, tier = 'cold', updated_at = ?
                WHERE memory_id = ?
                """,
                (utc_now(), memory_id),
            )
        return self.get(memory_id)

    def restore_local(
        self,
        memory_id: str,
        cipher: bytes,
        nonce: bytes,
        key_id: str,
    ) -> MemoryRecord | None:
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE memories SET cipher = ?, nonce = ?, key_id = ?,
                    tier = 'warm', updated_at = ? WHERE memory_id = ?
                """,
                (cipher, nonce, key_id, utc_now(), memory_id),
            )
        return self.get(memory_id)

    def due_for_backup(self, interval_seconds: float, limit: int = 100) -> list[MemoryRecord]:
        cutoff = (datetime.now(UTC) - timedelta(seconds=interval_seconds)).isoformat()
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT m.* FROM memories m
                WHERE m.status = 'active'
                  AND m.cipher IS NOT NULL
                  AND COALESCE(
                    (SELECT MAX(r.acked_at) FROM memory_replicas r
                     WHERE r.memory_id = m.memory_id),
                    ''
                  ) < ?
                ORDER BY m.importance DESC, m.updated_at ASC
                LIMIT ?
                """,
                (cutoff, limit),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def backup_usage_bytes(self) -> int:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(size_bytes), 0) AS total FROM backup_blobs"
            ).fetchone()
        return int(row["total"])

    def backup_size(self, memory_id: str) -> int:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT size_bytes FROM backup_blobs WHERE memory_id = ?",
                (memory_id,),
            ).fetchone()
        return int(row["size_bytes"]) if row else 0

    def replica_endpoints(self, memory_id: str) -> list[tuple[str, str, str]]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT node_id, endpoint, failure_domain
                FROM memory_replicas WHERE memory_id = ?
                ORDER BY acked_at DESC
                """,
                (memory_id,),
            ).fetchall()
        return [
            (row["node_id"], row["endpoint"], row["failure_domain"]) for row in rows
        ]

    def list_all_active(self) -> list[MemoryRecord]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT * FROM memories WHERE status = 'active' ORDER BY memory_id"
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def list_namespace(self, namespace_id: str) -> list[MemoryRecord]:
        with self.database.connection() as connection:
            rows = connection.execute(
                """
                SELECT * FROM memories
                WHERE namespace_id = ? AND status != 'tombstoned'
                ORDER BY created_at, memory_id
                """,
                (namespace_id,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def save_backup(self, copy: BackupCopy) -> None:
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO backup_blobs(
                    memory_id, namespace_id, owner_id, content_hash, cipher,
                    nonce, key_id, size_bytes, source_node_id,
                    source_failure_domain, stored_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    content_hash = excluded.content_hash,
                    cipher = excluded.cipher,
                    nonce = excluded.nonce,
                    key_id = excluded.key_id,
                    size_bytes = excluded.size_bytes,
                    stored_at = excluded.stored_at
                """,
                (
                    copy.memory_id,
                    copy.namespace_id,
                    copy.owner_id,
                    copy.content_hash,
                    copy.cipher,
                    copy.nonce,
                    copy.key_id,
                    copy.size_bytes,
                    copy.source_node_id,
                    copy.source_failure_domain,
                    utc_now(),
                ),
            )

    def get_backup(self, memory_id: str) -> BackupCopy | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM backup_blobs WHERE memory_id = ?", (memory_id,)
            ).fetchone()
        if not row:
            return None
        return BackupCopy(
            memory_id=row["memory_id"],
            namespace_id=row["namespace_id"],
            owner_id=row["owner_id"],
            content_hash=row["content_hash"],
            cipher=row["cipher"],
            nonce=row["nonce"],
            key_id=row["key_id"],
            size_bytes=row["size_bytes"],
            source_node_id=row["source_node_id"],
            source_failure_domain=row["source_failure_domain"],
        )

    def delete_backup(self, memory_id: str) -> bool:
        with self.database.connection() as connection:
            cursor = connection.execute(
                "DELETE FROM backup_blobs WHERE memory_id = ?", (memory_id,)
            )
        return cursor.rowcount > 0

