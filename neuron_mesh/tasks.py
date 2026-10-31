from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import sqlite3
import time
import uuid
from dataclasses import dataclass

from .activity import ActivityBus
from .capabilities import CapabilityService
from .config import Settings
from .models import (
    NodeCapability,
    TaskAssignmentView,
    TaskCreateRequest,
    TaskView,
)
from .peers import PeerMesh
from .storage import Database

logger = logging.getLogger("neuron_mesh.tasks")


def _task_graph_id(task_id: str) -> str:
    return f"task:{task_id}"


def _node_graph_id(node_id: str) -> str:
    return f"node:{node_id}"


@dataclass(slots=True)
class TaskHost:
    node_id: str
    name: str
    endpoint: str
    capabilities: list[str]
    estimated_tflops: float
    failure_domain: str
    rtt_ms: float | None
    is_local: bool


def estimate_tflops(capability: NodeCapability) -> float:
    compute = capability.compute
    cpu_limit = capability.resource_pledge.cpu_limit_percent / 100
    ram_gib = compute.ram_available_bytes / 1024**3
    estimate = compute.cpu_count * cpu_limit * 1.4 + ram_gib * 0.35
    if compute.gpu_name:
        gpu_memory_gib = (compute.gpu_memory_bytes or 0) / 1024**3
        estimate += 45 + min(120, gpu_memory_gib * 2.5)
    return round(max(1.0, min(1_000.0, estimate)), 3)


class TaskStore:
    def __init__(self, database: Database) -> None:
        self.database = database

    def create(
        self,
        *,
        task_id: str,
        request: TaskCreateRequest,
        requester_host_id: str,
        requested_tflops: float,
        service_start_at: float,
        assignments: list[dict[str, object]],
    ) -> TaskView:
        now = time.time()
        with self.database.connection() as connection:
            connection.execute(
                """
                INSERT INTO tasks(
                    task_id, objective, requester_host_id, target_hosts,
                    max_parallel, requested_tflops, granted_tflops, status,
                    execution_mode, created_at, service_start_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 'pending', 'coordination', ?, ?, NULL)
                """,
                (
                    task_id,
                    request.objective,
                    requester_host_id,
                    request.target_hosts,
                    request.max_parallel,
                    requested_tflops,
                    now,
                    service_start_at,
                ),
            )
            connection.executemany(
                """
                INSERT INTO task_assignments(
                    assignment_id, task_id, sequence, stage_name, stage_weight,
                    capability, host_id, host_name, host_endpoint,
                    host_capacity_tflops, status, share_percent,
                    allocated_tflops, service_seconds, started_at, ends_at,
                    completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', 100, 0,
                          NULL, NULL, NULL, NULL)
                """,
                [
                    (
                        item["assignment_id"],
                        task_id,
                        item["sequence"],
                        item["stage_name"],
                        item["stage_weight"],
                        item["capability"],
                        item["host_id"],
                        item["host_name"],
                        item["host_endpoint"],
                        item["host_capacity_tflops"],
                    )
                    for item in assignments
                ],
            )
        self.rebalance()
        task = self.get(task_id)
        if task is None:
            raise RuntimeError("task disappeared after creation")
        return task

    def get(self, task_id: str) -> TaskView | None:
        with self.database.connection() as connection:
            row = connection.execute(
                "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
            ).fetchone()
            if row is None:
                return None
            assignments = connection.execute(
                """
                SELECT * FROM task_assignments
                WHERE task_id = ? ORDER BY sequence
                """,
                (task_id,),
            ).fetchall()
        return self._to_view(row, assignments)

    def list(
        self,
        *,
        limit: int = 20,
        include_complete: bool = True,
    ) -> list[TaskView]:
        where = "" if include_complete else "WHERE status IN ('pending', 'running')"
        with self.database.connection() as connection:
            rows = connection.execute(
                f"SELECT * FROM tasks {where} ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            task
            for row in rows
            if (task := self.get(str(row["task_id"]))) is not None
        ]

    def active(self) -> list[TaskView]:
        return self.list(limit=100, include_complete=False)

    @staticmethod
    def _to_view(
        row: sqlite3.Row,
        assignment_rows: list[sqlite3.Row],
    ) -> TaskView:
        assignments = [
            TaskAssignmentView(
                assignment_id=item["assignment_id"],
                sequence=item["sequence"],
                stage_name=item["stage_name"],
                capability=item["capability"],
                host_id=item["host_id"],
                host_name=item["host_name"],
                status=item["status"],
                share_percent=item["share_percent"],
                allocated_tflops=item["allocated_tflops"],
                service_seconds=item["service_seconds"],
                started_at=item["started_at"],
                ends_at=item["ends_at"],
                completed_at=item["completed_at"],
            )
            for item in assignment_rows
        ]
        return TaskView(
            task_id=row["task_id"],
            objective=row["objective"],
            requester_host_id=row["requester_host_id"],
            target_hosts=row["target_hosts"],
            participant_count=len({item.host_id for item in assignments}),
            max_parallel=row["max_parallel"],
            requested_tflops=row["requested_tflops"],
            granted_tflops=row["granted_tflops"],
            status=row["status"],
            execution_mode=row["execution_mode"],
            created_at=row["created_at"],
            service_start_at=row["service_start_at"],
            completed_at=row["completed_at"],
            assignments=assignments,
        )

    def finish_due(self, task_id: str, now: float) -> None:
        with self.database.connection() as connection:
            connection.execute(
                """
                UPDATE task_assignments
                SET status = 'done', completed_at = ?
                WHERE task_id = ? AND status = 'active' AND ends_at <= ?
                """,
                (now, task_id, now),
            )

    def active_assignments(self, task_id: str) -> list[sqlite3.Row]:
        with self.database.connection() as connection:
            return connection.execute(
                """
                SELECT * FROM task_assignments
                WHERE task_id = ? AND status = 'active'
                ORDER BY sequence
                """,
                (task_id,),
            ).fetchall()

    def pending_assignments(
        self,
        task_id: str,
        *,
        limit: int,
    ) -> list[sqlite3.Row]:
        with self.database.connection() as connection:
            return connection.execute(
                """
                SELECT * FROM task_assignments
                WHERE task_id = ? AND status = 'pending'
                ORDER BY sequence LIMIT ?
                """,
                (task_id, limit),
            ).fetchall()

    def activate(
        self,
        task_id: str,
        calls: list[dict[str, object]],
    ) -> None:
        with self.database.connection() as connection:
            connection.executemany(
                """
                UPDATE task_assignments
                SET status = 'active', service_seconds = ?, started_at = ?,
                    ends_at = ?
                WHERE assignment_id = ? AND task_id = ? AND status = 'pending'
                """,
                [
                    (
                        call["service_seconds"],
                        call["started_at"],
                        call["ends_at"],
                        call["assignment_id"],
                        task_id,
                    )
                    for call in calls
                ],
            )
            connection.execute(
                """
                UPDATE tasks SET status = 'running'
                WHERE task_id = ? AND status = 'pending'
                """,
                (task_id,),
            )
        self.rebalance()

    def refresh_state(self, task_id: str, now: float) -> TaskView | None:
        with self.database.connection() as connection:
            counts = connection.execute(
                """
                SELECT
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) AS active,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) AS failed
                FROM task_assignments WHERE task_id = ?
                """,
                (task_id,),
            ).fetchone()
            pending = int(counts["pending"] or 0)
            active = int(counts["active"] or 0)
            failed = int(counts["failed"] or 0)
            if active == 0 and pending == 0:
                status = "failed" if failed else "complete"
                connection.execute(
                    """
                    UPDATE tasks SET status = ?, completed_at = ?
                    WHERE task_id = ? AND status != ?
                    """,
                    (status, now, task_id, status),
                )
        task = self.get(task_id)
        if task is not None and task.status in {"complete", "failed"}:
            self.rebalance()
        return task

    def rebalance(self) -> None:
        with self.database.connection() as connection:
            tasks = connection.execute(
                """
                SELECT task_id, requested_tflops FROM tasks
                WHERE status IN ('pending', 'running')
                """
            ).fetchall()
            if not tasks:
                return
            task_rows = connection.execute(
                """
                SELECT a.* FROM task_assignments a
                JOIN tasks t ON t.task_id = a.task_id
                WHERE t.status IN ('pending', 'running')
                  AND a.status IN ('pending', 'active')
                ORDER BY a.task_id, a.sequence
                """
            ).fetchall()
            host_tasks: dict[str, set[str]] = {}
            for item in task_rows:
                host_tasks.setdefault(item["host_id"], set()).add(item["task_id"])
            by_task: dict[str, list[sqlite3.Row]] = {}
            for item in task_rows:
                by_task.setdefault(item["task_id"], []).append(item)
            for task in tasks:
                task_id = str(task["task_id"])
                rows = by_task.get(task_id, [])
                raw: list[tuple[sqlite3.Row, float]] = []
                raw_total = 0.0
                for item in rows:
                    count = max(1, len(host_tasks.get(item["host_id"], set())))
                    base_share = 100.0 / count
                    allocated = item["host_capacity_tflops"] * base_share / 100
                    raw_total += allocated
                    raw.append((item, base_share))
                requested = float(task["requested_tflops"])
                scale = min(1.0, requested / raw_total) if raw_total else 1.0
                granted = 0.0
                for item, base_share in raw:
                    share = base_share * scale
                    allocated = item["host_capacity_tflops"] * share / 100
                    granted += allocated
                    connection.execute(
                        """
                        UPDATE task_assignments
                        SET share_percent = ?, allocated_tflops = ?
                        WHERE assignment_id = ?
                        """,
                        (share, allocated, item["assignment_id"]),
                    )
                granted = min(requested, granted)
                connection.execute(
                    "UPDATE tasks SET granted_tflops = ? WHERE task_id = ?",
                    (granted, task_id),
                )


class TaskScheduler:
    """Persistent coordination-only task scheduler."""

    def __init__(
        self,
        settings: Settings,
        database: Database,
        identity_node_id: str,
        capabilities: CapabilityService,
        peers: PeerMesh,
        activity: ActivityBus,
    ) -> None:
        self.settings = settings
        self.database = database
        self.identity_node_id = identity_node_id
        self.capabilities = capabilities
        self.peers = peers
        self.activity = activity
        self.store = TaskStore(database)
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    def _hosts(self) -> list[TaskHost]:
        hosts: list[TaskHost] = []
        local = self.capabilities.current("resident")
        if local.admitted:
            hosts.append(
                TaskHost(
                    node_id=local.node_id,
                    name=local.node_name,
                    endpoint=self.settings.public_url,
                    capabilities=list(local.service_roles),
                    estimated_tflops=estimate_tflops(local),
                    failure_domain=local.network.failure_domain,
                    rtt_ms=0.0,
                    is_local=True,
                )
            )
        for peer in self.peers.list_live():
            capability = peer.capability
            if not capability.admitted or capability.resident_state in {
                "draining",
                "hibernated",
            }:
                continue
            hosts.append(
                TaskHost(
                    node_id=peer.node_id,
                    name=peer.name,
                    endpoint=peer.public_url,
                    capabilities=list(capability.service_roles),
                    estimated_tflops=estimate_tflops(capability),
                    failure_domain=peer.failure_domain,
                    rtt_ms=peer.rtt_ms,
                    is_local=False,
                )
            )
        return hosts

    @staticmethod
    def _select_hosts(hosts: list[TaskHost], target: int) -> list[TaskHost]:
        ranked = sorted(
            hosts,
            key=lambda host: (
                -host.estimated_tflops,
                host.rtt_ms if host.rtt_ms is not None else 10_000,
                host.node_id,
            ),
        )
        selected: list[TaskHost] = []
        domains: set[str] = set()
        while ranked and len(selected) < min(target, len(hosts)):
            ranked.sort(
                key=lambda host: (
                    0 if host.failure_domain not in domains else 1,
                    -host.estimated_tflops,
                    host.rtt_ms if host.rtt_ms is not None else 10_000,
                )
            )
            host = ranked.pop(0)
            selected.append(host)
            domains.add(host.failure_domain)
        return selected

    async def create(self, request: TaskCreateRequest) -> TaskView:
        async with self._lock:
            hosts = self._hosts()
            if not hosts:
                raise ValueError("no admitted task hosts are available")
            selected = self._select_hosts(hosts, request.target_hosts)
            assignment_count = max(len(selected), len(request.stages))
            assignments: list[dict[str, object]] = []
            for sequence in range(assignment_count):
                stage = request.stages[sequence % len(request.stages)]
                candidates = [
                    host
                    for host in selected
                    if stage.capability in host.capabilities
                ] or selected
                host = candidates[sequence % len(candidates)]
                assignments.append(
                    {
                        "assignment_id": uuid.uuid4().hex,
                        "sequence": sequence,
                        "stage_name": stage.name,
                        "stage_weight": stage.weight,
                        "capability": stage.capability,
                        "host_id": host.node_id,
                        "host_name": host.name,
                        "host_endpoint": host.endpoint,
                        "host_capacity_tflops": host.estimated_tflops,
                    }
                )
            default_request = sum(host.estimated_tflops for host in selected) * 0.6
            requested_tflops = request.requested_tflops or max(1.0, default_request)
            task_id = uuid.uuid4().hex
            now = time.time()
            task = self.store.create(
                task_id=task_id,
                request=request,
                requester_host_id=self.identity_node_id,
                requested_tflops=requested_tflops,
                service_start_at=now + 2.0,
                assignments=assignments,
            )
            self.activity.record_many(
                _node_graph_id(self.identity_node_id),
                [_task_graph_id(task_id)],
                "request",
                detail={
                    "en": (
                        f"Requested {requested_tflops:.1f} TF from "
                        f"{len(selected)} hosts for {len(request.stages)} stages"
                    ),
                    "zh": (
                        f"为 {len(request.stages)} 个阶段向 "
                        f"{len(selected)} 台主机申请 {requested_tflops:.1f} TF"
                    ),
                },
                duration=2.0,
            )
            return task

    def get(self, task_id: str) -> TaskView | None:
        return self.store.get(task_id)

    def list(self, *, limit: int = 20, include_complete: bool = True) -> list[TaskView]:
        return self.store.list(limit=limit, include_complete=include_complete)

    def _service_seconds(self, task_id: str, assignment: sqlite3.Row) -> float:
        digest = hashlib.sha256(
            f"{task_id}:{assignment['sequence']}:{assignment['host_id']}".encode()
        ).digest()
        jitter = 0.78 + (digest[0] / 255) * 0.66
        allocated = max(0.5, float(assignment["allocated_tflops"]))
        duration = (
            0.65 + 5.4 / math.sqrt(allocated + 1)
        ) * float(assignment["stage_weight"]) * jitter
        return max(0.65, min(8.0, duration))

    async def tick(self, now: float | None = None) -> None:
        current = now if now is not None else time.time()
        async with self._lock:
            active_tasks = self.store.active()
            for task in active_tasks:
                if current < task.service_start_at:
                    continue
                self.store.finish_due(task.task_id, current)
                running = self.store.active_assignments(task.task_id)
                free_slots = max(0, task.max_parallel - len(running))
                if free_slots:
                    pending = self.store.pending_assignments(
                        task.task_id,
                        limit=free_slots,
                    )
                    calls: list[dict[str, object]] = []
                    for assignment in pending:
                        duration = self._service_seconds(task.task_id, assignment)
                        calls.append(
                            {
                                "assignment_id": assignment["assignment_id"],
                                "started_at": current,
                                "ends_at": current + duration,
                                "service_seconds": duration,
                            }
                        )
                        self.activity.record_many(
                            _task_graph_id(task.task_id),
                            [_node_graph_id(str(assignment["host_id"]))],
                            "task",
                            detail={
                                "en": (
                                    f"Async call {assignment['sequence'] + 1}/"
                                    f"{len(task.assignments)} · "
                                    f"{assignment['stage_name']} · "
                                    f"service {duration:.1f}s"
                                ),
                                "zh": (
                                    f"异步调用 {assignment['sequence'] + 1}/"
                                    f"{len(task.assignments)} · "
                                    f"{assignment['stage_name']} · "
                                    f"服务 {duration:.1f} 秒"
                                ),
                            },
                            duration=duration,
                        )
                    if calls:
                        self.store.activate(task.task_id, calls)
                self.store.refresh_state(task.task_id, current)

    async def _run(self) -> None:
        while not self._stop.is_set():
            try:
                await self.tick()
            except Exception:
                logger.exception("task scheduler tick failed")
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=0.32)
            except TimeoutError:
                continue

    def start(self) -> None:
        if self._task is None:
            self._stop.clear()
            self._task = asyncio.create_task(self._run(), name="task-scheduler")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            await self._task
            self._task = None

