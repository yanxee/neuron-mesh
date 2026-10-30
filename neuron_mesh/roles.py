from __future__ import annotations

import json

from .models import RoleCreateRequest, RoleView
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

