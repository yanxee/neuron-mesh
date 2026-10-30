from pathlib import Path

import pytest

from neuron_mesh.capabilities import CapabilityService
from neuron_mesh.config import Settings
from neuron_mesh.models import PeerAnnouncement
from neuron_mesh.peers import PeerMesh
from neuron_mesh.security import NodeIdentity
from neuron_mesh.storage import Database


def create_mesh(tmp_path: Path, name: str, port: int, domain: str):
    data_dir = tmp_path / name
    data_dir.mkdir()
    settings = Settings(
        node_name=name,
        data_dir=data_dir,
        public_url=f"http://127.0.0.1:{port}",
        shared_token="test-token",
        offline=True,
        failure_domain=domain,
    )
    database = Database(data_dir / "node.db")
    database.initialize()
    identity = NodeIdentity(data_dir)
    capabilities = CapabilityService(settings, identity)
    return settings, PeerMesh(settings, database, identity, capabilities)


@pytest.mark.asyncio
async def test_peer_announcement_is_verified_and_selectable(tmp_path: Path) -> None:
    _, mesh_a = create_mesh(tmp_path, "node-a", 9001, "domain-a")
    _, mesh_b = create_mesh(tmp_path, "node-b", 9002, "domain-b")

    peer = mesh_a.register(mesh_b.announcement())
    selected = await mesh_a.choose("neuron-echo-1")

    assert peer.node_id == mesh_b.identity.node_id
    assert selected is not None
    assert selected.public_url == "http://127.0.0.1:9002"

    announcement = mesh_b.announcement()
    tampered = announcement.model_dump(mode="json")
    tampered["capability"]["node_name"] = "evil"
    with pytest.raises(ValueError):
        mesh_a.register(PeerAnnouncement.model_validate(tampered))

    await mesh_a.stop()
    await mesh_b.stop()

