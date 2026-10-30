from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "e2e-only-token-8f7c6b"


def request(
    method: str,
    url: str,
    *,
    body: dict[str, object] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, object]:
    merged = {"Authorization": f"Bearer {TOKEN}", **(headers or {})}
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        merged["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=merged)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_ready(url: str, process: subprocess.Popen[bytes], timeout: float = 20) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"node exited early with code {process.returncode}")
        try:
            with urllib.request.urlopen(f"{url}/healthz", timeout=1) as response:
                if json.loads(response.read())["status"] == "ok":
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.25)
    raise RuntimeError(f"node at {url} did not become ready")


def wait_networked(url: str, timeout: float = 30) -> dict[str, object]:
    deadline = time.time() + timeout
    last_status: dict[str, object] = {}
    while time.time() < deadline:
        try:
            last_status = request("GET", f"{url}/v1/network/status")
            if last_status.get("mode") == "networked":
                return last_status
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            pass
        time.sleep(0.5)
    raise RuntimeError(f"node at {url} did not join the mesh: {last_status}")


def start_node(
    python: str, root: Path, name: str, port: int, peer_port: int, domain: str
) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env.update(
        {
            "NEURON_NODE_NAME": name,
            "NEURON_DATA_DIR": str(root / name),
            "NEURON_PUBLIC_URL": f"http://127.0.0.1:{port}",
            "NEURON_BOOTSTRAP_PEERS": f"http://127.0.0.1:{peer_port}",
            "NEURON_SHARED_TOKEN": TOKEN,
            "NEURON_DEVICE_CLASS": "server",
            "NEURON_FAILURE_DOMAIN": domain,
            "NEURON_OFFLINE": "false",
            "NEURON_BACKUP_INTERVAL_SECONDS": "5",
            "NEURON_STORAGE_MAX_BYTES": str(5 * 1024**3),
            "NEURON_STORAGE_PLEDGE_BYTES": str(512 * 1024**2),
        }
    )
    return subprocess.Popen(
        [
            python,
            "-m",
            "neuron_mesh",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main() -> None:
    python = str(ROOT / ".venv" / "Scripts" / "python.exe")
    if not Path(python).exists():
        python = sys.executable

    with tempfile.TemporaryDirectory(prefix="neuron-mesh-e2e-") as temp:
        data_root = Path(temp)
        a = start_node(python, data_root, "node-a", 18081, 18082, "domain-a")
        b = start_node(python, data_root, "node-b", 18082, 18081, "domain-b")
        try:
            wait_ready("http://127.0.0.1:18081", a)
            wait_ready("http://127.0.0.1:18082", b)

            status = wait_networked("http://127.0.0.1:18082")
            assert status["mode"] == "networked"
            assert status["online_peer_count"] >= 1

            memory = request(
                "POST",
                "http://127.0.0.1:18082/v1/memory/write?replicate=true",
                body={
                    "namespace_id": "ns-e2e",
                    "owner_id": "owner-e2e",
                    "role_id": "agent://e2e",
                    "kind": "fact",
                    "text": "分布式记忆必须在另一个故障域保留密文副本。",
                    "summary": "跨故障域密文备份",
                    "importance": 5,
                },
            )
            backup = request(
                "GET",
                f"http://127.0.0.1:18081/v1/internal/backups/{memory['memory_id']}",
            )
            assert backup["content_hash"] == memory["content_hash"]
            assert memory["durability"] in {"D2", "D3"}
            assert memory["replicas"]

            chat = request(
                "POST",
                "http://127.0.0.1:18082/v1/chat/completions",
                headers={"X-Neuron-Route": "network"},
                body={
                    "model": "neuron-echo-1",
                    "messages": [{"role": "user", "content": "远端执行测试"}],
                },
            )
            assert chat["x_neuron"]["mode"] == "networked"
            assert chat["x_neuron"]["executed_by"] != status["node_id"]

            relocated = request(
                "POST",
                f"http://127.0.0.1:18082/v1/memory/{memory['memory_id']}/relocate",
            )
            assert relocated["local_content"] is False

            restored = request(
                "GET", f"http://127.0.0.1:18082/v1/memory/{memory['memory_id']}"
            )
            assert restored["local_content"] is True
            assert "分布式记忆" in restored["text"]

            print(
                json.dumps(
                    {
                        "mode": status["mode"],
                        "online_peers": status["online_peer_count"],
                        "durability": memory["durability"],
                        "replicas": memory["replicas"],
                        "remote_node": chat["x_neuron"]["executed_by"],
                        "cold_restore": "ok",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
        finally:
            for process in (a, b):
                if process.poll() is None:
                    process.terminate()
            for process in (a, b):
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


if __name__ == "__main__":
    main()

