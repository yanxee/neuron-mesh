from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Literal

ActivityKind = Literal[
    "discovery", "compute", "storage", "role", "request", "task"
]


class ActivityBus:
    """Small in-memory activity stream for the local graph view."""

    def __init__(self, max_events: int = 256, retention_seconds: float = 30.0) -> None:
        self._events: deque[dict[str, object]] = deque(maxlen=max_events)
        self._retention_seconds = retention_seconds
        self._lock = threading.Lock()

    def record(
        self,
        source_id: str,
        target_id: str,
        kind: ActivityKind,
        *,
        detail: str | dict[str, str] = "",
    ) -> dict[str, object]:
        return self.record_many(
            source_id,
            [target_id],
            kind,
            detail=detail,
        )

    def record_many(
        self,
        source_id: str,
        target_ids: list[str],
        kind: ActivityKind,
        *,
        detail: str | dict[str, str] = "",
        duration: float | None = None,
    ) -> dict[str, object]:
        targets = [target for target in target_ids if target]
        if not targets:
            raise ValueError("activity requires at least one target")
        now = time.time()
        with self._lock:
            if self._events:
                previous = self._events[-1]
                if (
                    previous["source"] == source_id
                    and previous.get("targets", [previous["target"]]) == targets
                    and previous["kind"] == kind
                    and now - float(previous["occurred_at"]) < 1.5
                ):
                    return dict(previous)
            event = {
                "id": uuid.uuid4().hex,
                "source": source_id,
                "target": targets[0],
                "targets": targets,
                "kind": kind,
                "detail": detail,
                "duration": duration,
                "occurred_at": now,
            }
            self._events.append(event)
            return dict(event)

    def snapshot(self, max_age_seconds: float = 15.0) -> list[dict[str, object]]:
        cutoff = time.time() - min(max_age_seconds, self._retention_seconds)
        with self._lock:
            while self._events and float(self._events[0]["occurred_at"]) < cutoff:
                self._events.popleft()
            return [dict(event) for event in self._events]
