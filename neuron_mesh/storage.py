from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class Database:
    def __init__(self, path: Path) -> None:
        self.path = path

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS peers (
                    node_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    public_url TEXT NOT NULL,
                    failure_domain TEXT NOT NULL,
                    public_key_b64 TEXT NOT NULL,
                    signature_b64 TEXT NOT NULL,
                    capability_json TEXT NOT NULL,
                    last_seen TEXT NOT NULL,
                    rtt_ms REAL
                );

                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    namespace_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    role_id TEXT,
                    kind TEXT NOT NULL,
                    cipher BLOB,
                    nonce BLOB,
                    key_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    importance INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    source_refs TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    durability TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS memories_namespace
                    ON memories(namespace_id, status, tier);

                CREATE TABLE IF NOT EXISTS memory_terms (
                    memory_id TEXT NOT NULL REFERENCES memories(memory_id)
                        ON DELETE CASCADE,
                    term_hash TEXT NOT NULL,
                    PRIMARY KEY(memory_id, term_hash)
                );

                CREATE INDEX IF NOT EXISTS memory_terms_hash
                    ON memory_terms(term_hash);

                CREATE TABLE IF NOT EXISTS memory_replicas (
                    memory_id TEXT NOT NULL REFERENCES memories(memory_id)
                        ON DELETE CASCADE,
                    node_id TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    failure_domain TEXT NOT NULL,
                    acked_at TEXT NOT NULL,
                    PRIMARY KEY(memory_id, node_id)
                );

                CREATE TABLE IF NOT EXISTS backup_blobs (
                    memory_id TEXT PRIMARY KEY,
                    namespace_id TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    cipher BLOB NOT NULL,
                    nonce BLOB NOT NULL,
                    key_id TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    source_node_id TEXT NOT NULL,
                    source_failure_domain TEXT NOT NULL,
                    stored_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS roles (
                    role_id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    namespace_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_bindings_json TEXT NOT NULL,
                    allowed_actions_json TEXT NOT NULL,
                    primary_host_id TEXT NOT NULL,
                    state_version INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    objective TEXT NOT NULL,
                    requester_host_id TEXT NOT NULL,
                    target_hosts INTEGER NOT NULL,
                    max_parallel INTEGER NOT NULL,
                    requested_tflops REAL NOT NULL,
                    granted_tflops REAL NOT NULL,
                    status TEXT NOT NULL,
                    execution_mode TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    service_start_at REAL NOT NULL,
                    completed_at REAL
                );

                CREATE INDEX IF NOT EXISTS tasks_status
                    ON tasks(status, created_at);

                CREATE TABLE IF NOT EXISTS task_assignments (
                    assignment_id TEXT PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES tasks(task_id)
                        ON DELETE CASCADE,
                    sequence INTEGER NOT NULL,
                    stage_name TEXT NOT NULL,
                    stage_weight REAL NOT NULL,
                    capability TEXT NOT NULL,
                    host_id TEXT NOT NULL,
                    host_name TEXT NOT NULL,
                    host_endpoint TEXT NOT NULL,
                    host_capacity_tflops REAL NOT NULL,
                    status TEXT NOT NULL,
                    share_percent REAL NOT NULL,
                    allocated_tflops REAL NOT NULL,
                    service_seconds REAL,
                    started_at REAL,
                    ends_at REAL,
                    completed_at REAL,
                    UNIQUE(task_id, sequence)
                );

                CREATE INDEX IF NOT EXISTS task_assignments_task
                    ON task_assignments(task_id, sequence);

                CREATE INDEX IF NOT EXISTS task_assignments_status
                    ON task_assignments(status, ends_at);
                """
            )

    def checkpoint(self) -> None:
        with self.connection() as connection:
            connection.execute("PRAGMA wal_checkpoint(FULL)")
