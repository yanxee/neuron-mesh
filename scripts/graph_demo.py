from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "graph-demo-token"


def request(
    method: str,
    url: str,
    *,
    payload: dict[str, object] | None = None,
) -> object:
    data = None
    headers = {"Authorization": f"Bearer {TOKEN}"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for(url: str, path: str, predicate, timeout: float = 30) -> dict[str, object]:
    deadline = time.time() + timeout
    last: dict[str, object] = {}
    while time.time() < deadline:
        try:
            value = request("GET", f"{url}{path}")
            if isinstance(value, dict):
                last = value
                if predicate(last):
                    return last
        except OSError:
            pass
        time.sleep(0.35)
    raise RuntimeError(f"timed out waiting for {url}{path}: {last}")


def start_node(
    python: str,
    data_root: Path,
    *,
    name: str,
    port: int,
    peer_port: int,
    domain: str,
) -> subprocess.Popen[bytes]:
    env = os.environ.copy()
    env.update(
        {
            "NEURON_NODE_NAME": name,
            "NEURON_DATA_DIR": str(data_root / name),
            "NEURON_PUBLIC_URL": f"http://127.0.0.1:{port}",
            "NEURON_BOOTSTRAP_PEERS": f"http://127.0.0.1:{peer_port}",
            "NEURON_SHARED_TOKEN": TOKEN,
            "NEURON_DEVICE_CLASS": "server",
            "NEURON_FAILURE_DOMAIN": domain,
            "NEURON_BACKUP_INTERVAL_SECONDS": "5",
            "NEURON_PEER_REFRESH_SECONDS": "5",
            "NEURON_STORAGE_PLEDGE_BYTES": str(512 * 1024**2),
            "NEURON_STORAGE_MAX_BYTES": str(5 * 1024**3),
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
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a two-node graph demo")
    parser.add_argument("--seconds", type=float, default=0)
    parser.add_argument("--open", action="store_true")
    args = parser.parse_args()

    python = str(ROOT / ".venv" / "Scripts" / "python.exe")
    if not Path(python).exists():
        python = sys.executable

    with tempfile.TemporaryDirectory(prefix="neuron-graph-demo-") as temp:
        root = Path(temp)
        first = start_node(
            python, root, name="london-node", port=18081, peer_port=18082, domain="london"
        )
        second = start_node(
            python, root, name="tokyo-node", port=18082, peer_port=18081, domain="tokyo"
        )
        try:
            wait_for("http://127.0.0.1:18081", "/readyz", lambda data: data.get("ready"))
            wait_for("http://127.0.0.1:18082", "/readyz", lambda data: data.get("ready"))
            wait_for(
                "http://127.0.0.1:18082",
                "/v1/network/status",
                lambda data: data.get("mode") == "networked",
            )

            roles = [
                (
                    "http://127.0.0.1:18081",
                    "agent://archivist",
                    "Archive Keeper / 档案守护者",
                ),
                (
                    "http://127.0.0.1:18082",
                    "agent://cartographer",
                    "World Cartographer / 世界制图者",
                ),
            ]
            for endpoint, role_id, display_name in roles:
                request(
                    "POST",
                    f"{endpoint}/v1/roles",
                    payload={
                        "role_id": role_id,
                        "owner_id": "graph-demo-owner",
                        "namespace_id": "graph-demo",
                        "display_name": display_name,
                        "allowed_actions": ["speak", "gaze", "gesture"],
                    },
                )

            request(
                "POST",
                "http://127.0.0.1:18082/v1/memory/write?replicate=true",
                payload={
                    "namespace_id": "graph-demo",
                    "owner_id": "graph-demo-owner",
                    "role_id": "agent://cartographer",
                    "kind": "fact",
                    "text": "The graph should show a live compute pulse.",
                    "summary": "Graph demo memory",
                    "importance": 4,
                },
            )
            request(
                "POST",
                "http://127.0.0.1:18082/v1/chat/completions",
                payload={
                    "model": "neuron-echo-1",
                    "messages": [{"role": "user", "content": "Show a compute pulse"}],
                },
            )

            graph_url = "http://127.0.0.1:18082/graph"
            print(f"Graph demo: {graph_url}")
            print(
                "The dashboard asks for the bearer token "
                f"'{TOKEN}' because the graph data remains authenticated."
            )
            if args.open:
                webbrowser.open(graph_url)
            if args.seconds > 0:
                time.sleep(args.seconds)
            else:
                print("Press Ctrl+C to stop both nodes.")
                while True:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            for process in (first, second):
                if process.poll() is None:
                    process.terminate()
            for process in (first, second):
                try:
                    process.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    process.kill()


if __name__ == "__main__":
    main()
