from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from neuron_mesh.api import create_app
from neuron_mesh.config import Settings


def test_graph_dashboard_exposes_roles_relations_and_activity(tmp_path: Path) -> None:
    settings = Settings(
        node_name="graph-test",
        data_dir=tmp_path,
        shared_token="secret",
        offline=True,
    )
    headers = {"Authorization": "Bearer secret"}

    with TestClient(create_app(settings)) as client:
        page = client.get("/graph")
        assert page.status_code == 200
        assert "NeuronMesh Graph" in page.text
        assert "/v1/observability/graph" in page.text
        assert "graphCanvas" in page.text
        assert "实时主机、角色与活动" in page.text
        assert "fleet50" in page.text
        assert "buildFleetPlan" in page.text
        assert "redundancy_peer_ids" in page.text
        assert "taskTemplates" in page.text
        assert "activateDemoTask" in page.text
        assert "event.targets" in page.text

        assert client.get("/v1/observability/graph").status_code == 401
        assert client.get("/v1/roles/summary").status_code == 401

        role = client.post(
            "/v1/roles",
            headers=headers,
            json={
                "role_id": "agent://graph",
                "owner_id": "owner-graph",
                "namespace_id": "ns-graph",
                "display_name": "Graph Researcher",
                "allowed_actions": ["speak", "gesture"],
            },
        )
        assert role.status_code == 200

        memory = client.post(
            "/v1/memory/write",
            headers=headers,
            json={
                "namespace_id": "ns-graph",
                "owner_id": "owner-graph",
                "role_id": "agent://graph",
                "kind": "fact",
                "text": "Graph roles should be linked to their host.",
            },
        )
        assert memory.status_code == 200

        summaries = client.get("/v1/roles/summary", headers=headers)
        assert summaries.status_code == 200
        assert summaries.json()[0]["role_id"] == "agent://graph"
        assert "owner_id" not in summaries.json()[0]
        assert "namespace_id" not in summaries.json()[0]

        graph = client.get("/v1/observability/graph", headers=headers)
        assert graph.status_code == 200
        payload = graph.json()
        assert payload["summary"]["hosts"] == 1
        assert payload["summary"]["roles"] == 1

        node_ids = {node["id"] for node in payload["nodes"]}
        assert "role:agent://graph" in node_ids
        local_node = next(node for node in payload["nodes"] if node["is_local"])
        assert {
            "source": local_node["id"],
            "target": "role:agent://graph",
            "kind": "hosts",
        }.items() <= next(
            edge for edge in payload["edges"] if edge["kind"] == "hosts"
        ).items()
        assert {event["kind"] for event in payload["activity"]} >= {"role"}
