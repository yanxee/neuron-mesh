from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from neuron_mesh.activity import ActivityBus
from neuron_mesh.api import create_app
from neuron_mesh.capabilities import CapabilityService
from neuron_mesh.config import Settings
from neuron_mesh.models import TaskCreateRequest
from neuron_mesh.peers import PeerMesh
from neuron_mesh.security import NodeIdentity
from neuron_mesh.storage import Database
from neuron_mesh.tasks import TaskScheduler


def _request() -> dict[str, object]:
    return {
        "objective": "Research a distributed systems question",
        "stages": [
            {"name": "Plan", "capability": "full-model"},
            {"name": "Retrieve", "capability": "cache"},
            {"name": "Infer", "capability": "inference"},
            {"name": "Verify", "capability": "checkpoint"},
        ],
        "target_hosts": 1,
        "max_parallel": 1,
        "requested_tflops": 100,
    }


def test_task_api_and_graph_node(tmp_path: Path) -> None:
    settings = Settings(
        node_name="task-api",
        data_dir=tmp_path,
        shared_token="secret",
        offline=True,
    )
    headers = {"Authorization": "Bearer secret"}

    with TestClient(create_app(settings)) as client:
        assert client.get("/v1/tasks").status_code == 401
        created = client.post("/v1/tasks", headers=headers, json=_request())
        assert created.status_code == 200
        task = created.json()
        assert task["status"] in {"pending", "running"}
        assert task["execution_mode"] == "coordination"
        assert task["participant_count"] == 1
        assert len(task["assignments"]) == 4
        assert task["granted_tflops"] <= task["requested_tflops"]

        fetched = client.get(f"/v1/tasks/{task['task_id']}", headers=headers)
        assert fetched.status_code == 200
        listed = client.get("/v1/tasks", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["task_id"] == task["task_id"]

        graph = client.get("/v1/observability/graph", headers=headers).json()
        task_node = next(
            node for node in graph["nodes"] if node["id"] == f"task:{task['task_id']}"
        )
        assert task_node["kind"] == "task"
        assert task_node["target_coverage"] == 1
        assert task_node["parallel_width"] == 1
        assert graph["summary"]["tasks"] >= 1


def test_scheduler_uses_independent_asynchronous_service_windows(
    tmp_path: Path,
) -> None:
    settings = Settings(
        node_name="task-scheduler",
        data_dir=tmp_path,
        shared_token="secret",
        offline=True,
    )
    settings.ensure_data_dir()
    database = Database(settings.database_path)
    database.initialize()
    identity = NodeIdentity(settings.data_dir)
    capabilities = CapabilityService(settings, identity)
    target_settings = Settings(
        node_name="task-target",
        data_dir=tmp_path / "target",
        shared_token="secret",
        offline=True,
        failure_domain="target-domain",
    )
    target_settings.ensure_data_dir()
    target_database = Database(target_settings.database_path)
    target_database.initialize()
    target_identity = NodeIdentity(target_settings.data_dir)
    target_capabilities = CapabilityService(target_settings, target_identity)

    async def run() -> None:
        peers = PeerMesh(settings, database, identity, capabilities)
        target_peers = PeerMesh(
            target_settings,
            target_database,
            target_identity,
            target_capabilities,
        )
        scheduler = TaskScheduler(
            settings,
            database,
            identity.node_id,
            capabilities,
            peers,
            ActivityBus(),
        )
        try:
            peers.register(target_peers.announcement())
            payload = _request()
            payload["target_hosts"] = 2
            task = await scheduler.create(TaskCreateRequest.model_validate(payload))
            assert task.participant_count == 2
            assert len({item.host_id for item in task.assignments}) == 2
            await scheduler.tick(now=task.service_start_at + 0.01)
            first = scheduler.get(task.task_id)
            assert first is not None
            first_active = [item for item in first.assignments if item.status == "active"]
            assert len(first_active) == 1
            first_duration = first_active[0].service_seconds
            first_end = first_active[0].ends_at
            assert first_duration is not None and first_end is not None

            await scheduler.tick(now=first_end + 0.01)
            second = scheduler.get(task.task_id)
            assert second is not None
            assert sum(item.status == "done" for item in second.assignments) == 1
            second_active = [item for item in second.assignments if item.status == "active"]
            assert len(second_active) == 1
            assert second_active[0].service_seconds is not None
            assert second_active[0].service_seconds != first_duration
        finally:
            await target_peers.stop()
            await peers.stop()

    asyncio.run(run())
