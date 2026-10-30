from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .models import AvatarIntentRequest, SpatialEvent, SpatialSessionOpen
from .roles import RoleStore


@dataclass(slots=True)
class SpatialSession:
    session_id: str
    role_id: str
    owner_id: str
    space_id: str
    frame_id: str
    privacy_mode: str
    created_at: float
    events: list[dict[str, Any]] = field(default_factory=list)


class SpatialManager:
    def __init__(self, roles: RoleStore) -> None:
        self.roles = roles
        self.sessions: dict[str, SpatialSession] = {}

    def open(self, request: SpatialSessionOpen) -> SpatialSession:
        role = self.roles.get(request.role_id)
        if role is None:
            raise ValueError("role not found")
        if role.owner_id != request.owner_id:
            raise PermissionError("owner does not match role")
        session_id = uuid.uuid4().hex
        session = SpatialSession(
            session_id=session_id,
            role_id=request.role_id,
            owner_id=request.owner_id,
            space_id=request.space_id,
            frame_id=request.frame_id,
            privacy_mode=request.privacy_mode,
            created_at=time.time(),
        )
        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> SpatialSession:
        try:
            return self.sessions[session_id]
        except KeyError as exc:
            raise ValueError("spatial session not found") from exc

    def close(self, session_id: str) -> None:
        session = self.get(session_id)
        self.sessions.pop(session_id, None)
        for event in session.events:
            event.clear()

    def add_event(self, session_id: str, event: SpatialEvent) -> dict[str, Any]:
        session = self.get(session_id)
        if event.frame_id not in {session.frame_id, "local", "world"}:
            raise ValueError("event frame is not declared by the session")
        stored = {
            "event_id": uuid.uuid4().hex,
            "received_at": time.time(),
            "untrusted": True,
            **event.model_dump(mode="json"),
        }
        session.events.append(stored)
        if len(session.events) > 100:
            session.events.pop(0)
        return stored

    def submit_intent(
        self, session_id: str, intent: AvatarIntentRequest
    ) -> dict[str, Any]:
        session = self.get(session_id)
        role = self.roles.get(session.role_id)
        if role is None:
            raise ValueError("role not found")
        allowed = intent.action in role.allowed_actions
        high_impact = intent.action not in {"speak", "gaze", "gesture"}
        explicit_token_valid = bool(
            high_impact
            and intent.permission_token
            and intent.permission_token.startswith("allow:")
        )
        accepted = allowed and (not high_impact or explicit_token_valid)
        return {
            "accepted": accepted,
            "action": intent.action,
            "reason": (
                "allowed"
                if accepted
                else "high-impact action requires a short-lived permission token"
                if allowed
                else "action is not granted to this role"
            ),
            "session_id": session_id,
            "role_id": session.role_id,
            "intent": intent.model_dump(mode="json"),
        }

