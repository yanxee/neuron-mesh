"""Two-node integration tests for streamed remote inference.

These tests start two real ``neuron_mesh serve`` subprocesses (the same
pattern as ``scripts/e2e_check.py``) and exercise gateway-to-gateway chat
streaming over HTTP:

- a streamed chat routed to a peer returns chunked SSE that reassembles
  into the peer's response, and the gateway records the remote execution;
- ``X-Neuron-Forwarded: 1`` stops a node from forwarding a request a
  second time (loop prevention);
- a client that disconnects mid-stream leaves the gateway healthy;
- a peer that accepts connections but never answers fails the forwarded
  request within the configured request timeout instead of hanging.

Starting real nodes makes these slower than the unit tests (tens of
seconds for the shared fixture).
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "stream-test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
MODEL = "neuron-echo-1"


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _node_env(root: Path, name: str, port: int, bootstrap_port: int | None,
              domain: str, extra: dict[str, str]) -> dict[str, str]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key.lower() not in {
            "http_proxy", "https_proxy", "all_proxy",
            "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        }
    }
    env.update(
        {
            "NEURON_NODE_NAME": name,
            "NEURON_DATA_DIR": str(root / name),
            "NEURON_PUBLIC_URL": f"http://127.0.0.1:{port}",
            "NEURON_BOOTSTRAP_PEERS": (
                f"http://127.0.0.1:{bootstrap_port}" if bootstrap_port else ""
            ),
            "NEURON_SHARED_TOKEN": TOKEN,
            "NEURON_DEVICE_CLASS": "server",
            "NEURON_FAILURE_DOMAIN": domain,
            "NEURON_OFFLINE": "false",
            "NEURON_STORAGE_MAX_BYTES": str(5 * 1024**3),
            "NEURON_STORAGE_PLEDGE_BYTES": str(512 * 1024**2),
            "NO_PROXY": "127.0.0.1,localhost",
            "no_proxy": "127.0.0.1,localhost",
        }
    )
    env.update(extra)
    return env


def _start_node(root: Path, name: str, port: int, bootstrap_port: int | None,
                domain: str, extra: dict[str, str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        [
            sys.executable, "-m", "neuron_mesh", "serve",
            "--host", "127.0.0.1", "--port", str(port),
        ],
        cwd=ROOT,
        env=_node_env(root, name, port, bootstrap_port, domain, extra),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _wait_ready(base_url: str, process: subprocess.Popen[bytes],
                timeout: float = 90) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"node at {base_url} exited with {process.returncode}")
        try:
            response = httpx.get(f"{base_url}/healthz", timeout=2)
            if response.json().get("status") == "ok":
                return
        except (httpx.HTTPError, ValueError):
            pass
        time.sleep(0.25)
    raise RuntimeError(f"node at {base_url} did not become ready")


def _network_status(base_url: str) -> dict:
    response = httpx.get(
        f"{base_url}/v1/network/status", headers=AUTH, timeout=5
    )
    response.raise_for_status()
    return response.json()


def _wait_networked(base_url: str, timeout: float = 90) -> dict:
    deadline = time.time() + timeout
    status: dict = {}
    while time.time() < deadline:
        try:
            status = _network_status(base_url)
            if status.get("online_peer_count", 0) >= 1:
                return status
        except httpx.HTTPError:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"node at {base_url} did not join the mesh: {status}")


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


@pytest.fixture(scope="module")
def mesh(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Two meshed nodes: A is the gateway, B prefers remote execution."""
    root = tmp_path_factory.mktemp("neuron-mesh-streaming")
    port_a, port_b = _free_port(), _free_port()
    node_a = _start_node(root, "node-a", port_a, port_b, "domain-a", {})
    node_b = _start_node(
        root, "node-b", port_b, port_a, "domain-b",
        {"NEURON_PREFER_REMOTE": "true"},
    )
    base_a, base_b = f"http://127.0.0.1:{port_a}", f"http://127.0.0.1:{port_b}"
    try:
        _wait_ready(base_a, node_a)
        _wait_ready(base_b, node_b)
        status_a = _wait_networked(base_a)
        status_b = _wait_networked(base_b)
        yield {
            "base_a": base_a,
            "base_b": base_b,
            "id_a": status_a["node_id"],
            "id_b": status_b["node_id"],
        }
    finally:
        _stop(node_a)
        _stop(node_b)


def _chat_payload(text: str, stream: bool = False) -> dict:
    return {
        "model": MODEL,
        "stream": stream,
        "messages": [{"role": "user", "content": text}],
    }


def test_streamed_remote_chat_is_chunked_and_recorded(mesh: dict) -> None:
    text = "stream hello"
    with httpx.Client(timeout=30) as client:
        with client.stream(
            "POST",
            f"{mesh['base_a']}/v1/chat/completions",
            headers={**AUTH, "X-Neuron-Route": "network"},
            json=_chat_payload(text, stream=True),
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")
            lines = [
                line for line in response.iter_lines() if line.startswith("data:")
            ]

    assert lines[-1] == "data: [DONE]"
    events = [json.loads(line[len("data: "):]) for line in lines[:-1]]
    content = "".join(
        event["choices"][0]["delta"].get("content", "") for event in events
    )
    # The peer's full response, re-chunked by the gateway into SSE deltas
    # (16 characters per chunk in the echo backend) plus a final stop event.
    assert content == f"neuron-mesh echo: {text}"
    assert len(events) >= 3
    assert events[-1]["choices"][0]["finish_reason"] == "stop"

    # Provenance: the gateway recorded a compute activity towards the peer.
    graph = httpx.get(
        f"{mesh['base_a']}/v1/observability/graph", headers=AUTH, timeout=5
    ).json()
    assert any(
        event["kind"] == "compute"
        and event["source"] == f"node:{mesh['id_a']}"
        and event["target"] == f"node:{mesh['id_b']}"
        and event["detail"] == MODEL
        for event in graph["activity"]
    )


def test_forwarded_header_prevents_second_forward(mesh: dict) -> None:
    # Control: node B prefers remote execution, so an unforwarded request
    # is executed by node A over the mesh.
    control = httpx.post(
        f"{mesh['base_b']}/v1/chat/completions",
        headers=AUTH,
        json=_chat_payload("loop check"),
        timeout=30,
    )
    assert control.status_code == 200
    assert control.json()["x_neuron"]["mode"] == "networked"
    assert control.json()["x_neuron"]["executed_by"] == mesh["id_a"]

    # The same request carrying X-Neuron-Forwarded must stay on node B:
    # if the header check in the chat endpoint were removed, B would
    # forward it to A again and executed_by would point at A.
    forwarded = httpx.post(
        f"{mesh['base_b']}/v1/chat/completions",
        headers={
            **AUTH,
            "X-Neuron-Forwarded": "1",
            "X-Neuron-Source-Node": mesh["id_a"],
        },
        json=_chat_payload("loop check"),
        timeout=30,
    )
    assert forwarded.status_code == 200
    assert forwarded.json()["x_neuron"]["mode"] == "local"
    assert forwarded.json()["x_neuron"]["executed_by"] == mesh["id_b"]


def test_client_disconnect_leaves_gateway_healthy(mesh: dict) -> None:
    with httpx.Client(timeout=30) as client:
        with client.stream(
            "POST",
            f"{mesh['base_a']}/v1/chat/completions",
            headers={**AUTH, "X-Neuron-Route": "network"},
            json=_chat_payload("disconnect check", stream=True),
        ) as response:
            assert response.status_code == 200
            first = next(
                line for line in response.iter_lines() if line.startswith("data:")
            )
            assert first.startswith("data: {")
        # Leaving the context closes the response mid-stream.

    health = httpx.get(f"{mesh['base_a']}/healthz", timeout=5)
    assert health.json() == {"status": "ok"}
    follow_up = httpx.post(
        f"{mesh['base_a']}/v1/chat/completions",
        headers=AUTH,
        json=_chat_payload("still alive"),
        timeout=30,
    )
    assert follow_up.status_code == 200
    assert "neuron-mesh echo" in follow_up.json()["choices"][0]["message"]["content"]


class _BlackHole:
    """TCP listener that accepts connections and never sends anything."""

    def __init__(self) -> None:
        self.port = _free_port()
        self._listener = socket.socket()
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", self.port))
        self._listener.listen()
        self._held: list[socket.socket] = []
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)

    def __enter__(self) -> "_BlackHole":
        self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._listener.close()
        for conn in self._held:
            conn.close()

    def _accept_loop(self) -> None:
        while True:
            try:
                conn, _ = self._listener.accept()
            except OSError:
                return
            self._held.append(conn)


def _fake_peer_announcement(tmp_path: Path, public_url: str) -> dict:
    """Build a valid signed peer announcement pointing at ``public_url``."""
    from neuron_mesh.capabilities import CapabilityService
    from neuron_mesh.config import Settings
    from neuron_mesh.peers import PeerMesh
    from neuron_mesh.security import NodeIdentity
    from neuron_mesh.storage import Database

    data_dir = tmp_path / "black-hole-peer"
    data_dir.mkdir()
    settings = Settings(
        node_name="black-hole",
        data_dir=data_dir,
        public_url=public_url,
        shared_token=TOKEN,
        offline=False,
        failure_domain="domain-bh",
    )
    database = Database(data_dir / "node.db")
    database.initialize()
    identity = NodeIdentity(data_dir)
    mesh = PeerMesh(settings, database, identity, CapabilityService(settings, identity))
    return mesh.announcement().model_dump(mode="json")


def test_unresponsive_peer_fails_within_request_timeout(
    tmp_path: Path,
) -> None:
    root = tmp_path / "gateway"
    root.mkdir()
    port = _free_port()
    node = _start_node(
        root, "node-c", port, None, "domain-c",
        {"NEURON_REQUEST_TIMEOUT_SECONDS": "2"},
    )
    base = f"http://127.0.0.1:{port}"
    try:
        _wait_ready(base, node)
        with _BlackHole() as hole:
            announcement = _fake_peer_announcement(
                tmp_path, f"http://127.0.0.1:{hole.port}"
            )
            registered = httpx.post(
                f"{base}/v1/peers/announce",
                headers=AUTH,
                json=announcement,
                timeout=10,
            )
            assert registered.status_code == 200

            started = time.monotonic()
            response = httpx.post(
                f"{base}/v1/chat/completions",
                headers={**AUTH, "X-Neuron-Route": "network"},
                json=_chat_payload("timeout check", stream=True),
                timeout=30,
            )
            elapsed = time.monotonic() - started

        # route=network surfaces the peer failure as 502, bounded by the
        # 2s request timeout rather than hanging on the silent peer.
        assert response.status_code == 502
        assert elapsed < 20
    finally:
        _stop(node)
