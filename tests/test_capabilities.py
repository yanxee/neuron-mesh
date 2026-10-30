from pathlib import Path

from neuron_mesh.capabilities import CapabilityService
from neuron_mesh.config import Settings
from neuron_mesh.security import NodeIdentity


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        node_name="test-node",
        data_dir=tmp_path,
        public_url="http://127.0.0.1:9000",
        shared_token="test-token",
        offline=True,
        failure_domain="domain-a",
    )


def test_signed_capability_contains_resource_pledge(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    settings.ensure_data_dir()
    identity = NodeIdentity(tmp_path)
    service = CapabilityService(settings, identity)

    capability = service.current()
    signed = service.signed()

    assert capability.node_id == identity.node_id
    pledge = capability.resource_pledge
    assert pledge.storage_max_bytes >= pledge.storage_min_bytes
    assert capability.derived_capacity[0].tier in {"strong", "weak"}
    assert signed["public_key_b64"] == identity.public_key_b64
    assert len(str(signed["signature_b64"])) > 20

