from __future__ import annotations

import hashlib
import json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .memory import MemoryStore
from .models import MemoryWriteRequest, RoleCreateRequest, RoleView
from .security import b64d, b64e
from .storage import Database, utc_now


class RoleStore:
    def __init__(self, database: Database, node_id: str) -> None:
        self.database = database
        self.node_id = node_id

    def create(self, request: RoleCreateRequest) -> RoleView:
        now = utc_now()
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO roles(
                    role_id, owner_id, namespace_id, display_name,
                    avatar_bindings_json, allowed_actions_json,
                    primary_host_id, state_version, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, 'active', ?, ?)
                ON CONFLICT(role_id) DO UPDATE SET
                    owner_id = excluded.owner_id,
                    namespace_id = excluded.namespace_id,
                    display_name = excluded.display_name,
                    avatar_bindings_json = excluded.avatar_bindings_json,
                    allowed_actions_json = excluded.allowed_actions_json,
                    state_version = roles.state_version + 1,
                    status = 'active',
                    updated_at = excluded.updated_at
                """,
                (
                    request.role_id,
                    request.owner_id,
                    request.namespace_id,
                    request.display_name,
                    json.dumps(request.avatar_bindings, ensure_ascii=False),
                    json.dumps(request.allowed_actions, ensure_ascii=False),
                    self.node_id,
                    now,
                    now,
                ),
            )
        role = self.get(request.role_id)
        if role is None:
            raise RuntimeError("role disappeared after creation")
        return role

    def get(self, role_id: str) -> RoleView | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM roles WHERE role_id = ?", (role_id,)
            ).fetchone()
        if not row:
            return None
        return RoleView(
            role_id=row["role_id"],
            owner_id=row["owner_id"],
            namespace_id=row["namespace_id"],
            display_name=row["display_name"],
            avatar_bindings=json.loads(row["avatar_bindings_json"]),
            allowed_actions=json.loads(row["allowed_actions_json"]),
            primary_host_id=row["primary_host_id"],
            state_version=row["state_version"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def set_status(self, role_id: str, status: str) -> RoleView | None:
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE roles SET status = ?, state_version = state_version + 1,
                    updated_at = ? WHERE role_id = ?
                """,
                (status, utc_now(), role_id),
            )
        return self.get(role_id)


class RoleMigrationService:
    def __init__(
        self,
        roles: RoleStore,
        memory: MemoryStore,
        *,
        node_id: str,
    ) -> None:
        self.roles = roles
        self.memory = memory
        self.node_id = node_id

    @staticmethod
    def _derive_key(secret: str, salt: bytes) -> bytes:
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        return PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=210_000,
        ).derive(digest)

    def export_package(
        self, role_id: str, target_node_id: str, transfer_secret: str
    ) -> dict[str, object]:
        role = self.roles.get(role_id)
        if role is None:
            raise ValueError("role not found")
        if target_node_id == self.node_id:
            raise ValueError("target node must be a different host")

        memories: list[dict[str, object]] = []
        for record in self.memory.list_namespace(role.namespace_id):
            text, summary = self.memory.decrypt(record)
            if text is None:
                continue
            memories.append(
                {
                    "role_id": role_id,
                    "kind": record.kind,
                    "text": text,
                    "summary": summary,
                    "source_refs": record.source_refs,
                    "importance": record.importance,
                    "status": record.status,
                }
            )

        payload = json.dumps(
            {
                "format": "neuron.role-migration/0.1",
                "source_node_id": self.node_id,
                "target_node_id": target_node_id,
                "role": role.model_dump(mode="json"),
                "memories": memories,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        import os

        salt = os.urandom(16)
        nonce = os.urandom(12)
        cipher = AESGCM(self._derive_key(transfer_secret, salt)).encrypt(
            nonce, payload, b"neuron.role-migration/0.1"
        )
        self.roles.set_status(role_id, "migrating")
        return {
            "format": "neuron.role-migration/0.1",
            "role_id": role_id,
            "source_node_id": self.node_id,
            "target_node_id": target_node_id,
            "salt_b64": b64e(salt),
            "nonce_b64": b64e(nonce),
            "cipher_b64": b64e(cipher),
            "created_at": utc_now(),
        }

    def import_package(
        self, package: dict[str, object], transfer_secret: str
    ) -> tuple[RoleView, int, str]:
        target_node_id = str(package["target_node_id"])
        if target_node_id != self.node_id:
            raise ValueError("migration package targets another node")
        salt = b64d(str(package["salt_b64"]))
        nonce = b64d(str(package["nonce_b64"]))
        cipher = b64d(str(package["cipher_b64"]))
        payload = json.loads(
            AESGCM(self._derive_key(transfer_secret, salt)).decrypt(
                nonce, cipher, b"neuron.role-migration/0.1"
            )
        )
        if payload["target_node_id"] != self.node_id:
            raise ValueError("encrypted migration payload targets another node")

        role_payload = payload["role"]
        request = RoleCreateRequest(
            role_id=role_payload["role_id"],
            owner_id=role_payload["owner_id"],
            namespace_id=role_payload["namespace_id"],
            display_name=role_payload.get("display_name", ""),
            avatar_bindings=role_payload.get("avatar_bindings", []),
            allowed_actions=role_payload.get("allowed_actions", []),
        )
        role = self.roles.create(request)
        imported = 0
        for item in payload["memories"]:
            record = self.memory.write(
                MemoryWriteRequest(
                    namespace_id=request.namespace_id,
                    owner_id=request.owner_id,
                    role_id=request.role_id,
                    kind=item["kind"],
                    text=item["text"],
                    summary=item.get("summary", ""),
                    source_refs=item.get("source_refs", []),
                    importance=item.get("importance", 3),
                )
            )
            if item.get("status") in {"sealed", "tombstoned"}:
                self.memory.set_status(record.memory_id, item["status"])
            imported += 1
        return role, imported, str(payload["source_node_id"])

