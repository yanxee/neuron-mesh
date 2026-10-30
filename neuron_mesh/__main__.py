from __future__ import annotations

import argparse
import json
import os

import httpx
import uvicorn

from .config import Settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="neuron-mesh")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve_parser = subparsers.add_parser("serve", help="start a neuron mesh node")
    serve_parser.add_argument("--host", default=None)
    serve_parser.add_argument("--port", type=int, default=None)
    serve_parser.add_argument("--reload", action="store_true")
    status_parser = subparsers.add_parser("status", help="read live node status")
    status_parser.add_argument("--url", default="")
    status_parser.add_argument("--token", default="")
    drain_parser = subparsers.add_parser("drain", help="prepare a safe node shutdown")
    drain_parser.add_argument("--url", default="")
    drain_parser.add_argument("--token", default="")
    subparsers.add_parser("settings", help="print effective non-secret settings")
    args = parser.parse_args()

    settings = Settings.from_env()
    if args.command == "settings":
        safe = {
            "node_name": settings.node_name,
            "data_dir": str(settings.data_dir),
            "public_url": settings.public_url,
            "model_id": settings.model_id,
            "device_class": settings.device_class,
            "failure_domain": settings.failure_domain,
            "availability_class": settings.availability_class,
            "offline": settings.offline,
            "bootstrap_peers": settings.bootstrap_peers,
            "local_backend_url": settings.local_backend_url,
        }
        print(json.dumps(safe, ensure_ascii=False, indent=2))
        return

    if args.command in {"status", "drain"}:
        base_url = (args.url or f"http://127.0.0.1:{settings.port}").rstrip("/")
        token = args.token or settings.shared_token
        path = "/v1/network/status" if args.command == "status" else "/v1/node/drain"
        method = "GET" if args.command == "status" else "POST"
        try:
            response = httpx.request(
                method,
                f"{base_url}{path}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise SystemExit(f"request failed: {exc}") from exc
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
        return

    if args.host:
        os.environ["NEURON_HOST"] = args.host
    if args.port:
        os.environ["NEURON_PORT"] = str(args.port)
        if not os.getenv("NEURON_PUBLIC_URL"):
            os.environ["NEURON_PUBLIC_URL"] = (
                f"http://{(args.host or settings.host)}:{args.port}"
            )
    uvicorn.run(
        "neuron_mesh.api:app",
        host=args.host or settings.host,
        port=args.port or settings.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

