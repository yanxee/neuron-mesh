from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in {None, ""} else default


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in {None, ""} else default


def _env_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip().rstrip("/") for item in value.split(",") if item.strip()]


def detect_device_class() -> str:
    machine = platform.machine().lower()
    system = platform.system().lower()
    if system in {"linux", "android"} and ("arm" in machine or "aarch" in machine):
        return "arm-edge"
    if system in {"windows", "darwin"}:
        return "desktop"
    if system == "linux":
        return "server"
    return "unknown"


@dataclass(slots=True)
class Settings:
    node_name: str
    data_dir: Path
    host: str = "127.0.0.1"
    port: int = 8000
    public_url: str = ""
    bootstrap_peers: list[str] = field(default_factory=list)
    shared_token: str = "development-only-token"
    model_id: str = "neuron-echo-1"
    device_class: str = field(default_factory=detect_device_class)
    failure_domain: str = "local"
    availability_class: str = "resident-constrained"
    service_roles: list[str] = field(
        default_factory=lambda: ["ingress", "full-model", "cache"]
    )
    local_backend_url: str = ""
    storage_pledge_bytes: int = 5 * 1024 * 1024 * 1024
    storage_max_bytes: int = 20 * 1024 * 1024 * 1024
    storage_safety_reserve_bytes: int = 2 * 1024 * 1024 * 1024
    cpu_limit_percent: float = 25.0
    daily_egress_bytes: int = 10 * 1024 * 1024 * 1024
    offline: bool = False
    prefer_remote: bool = False
    peer_refresh_seconds: float = 10.0
    backup_interval_seconds: float = 60.0
    request_timeout_seconds: float = 30.0
    hot_memory_limit_bytes: int = 2 * 1024 * 1024
    max_request_bytes: int = 10 * 1024 * 1024
    cors_origins: list[str] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> Settings:
        node_name = os.getenv("NEURON_NODE_NAME") or platform.node() or "neuron-node"
        data_dir = Path(os.getenv("NEURON_DATA_DIR", f"./data/{node_name}")).resolve()
        port = _env_int("NEURON_PORT", 8000)
        public_url = os.getenv(
            "NEURON_PUBLIC_URL", f"http://127.0.0.1:{port}"
        ).rstrip("/")
        return cls(
            node_name=node_name,
            data_dir=data_dir,
            host=os.getenv("NEURON_HOST", "127.0.0.1"),
            port=port,
            public_url=public_url,
            bootstrap_peers=_env_list("NEURON_BOOTSTRAP_PEERS"),
            shared_token=os.getenv("NEURON_SHARED_TOKEN", "development-only-token"),
            model_id=os.getenv("NEURON_MODEL_ID", "neuron-echo-1"),
            device_class=os.getenv("NEURON_DEVICE_CLASS", detect_device_class()),
            failure_domain=os.getenv("NEURON_FAILURE_DOMAIN", "local"),
            availability_class=os.getenv(
                "NEURON_AVAILABILITY_CLASS", "resident-constrained"
            ),
            service_roles=[
                item
                for item in os.getenv(
                    "NEURON_SERVICE_ROLES", "ingress,full-model,cache"
                ).split(",")
                if item
            ],
            local_backend_url=os.getenv("NEURON_LOCAL_BACKEND_URL", "").rstrip("/"),
            storage_pledge_bytes=_env_int(
                "NEURON_STORAGE_PLEDGE_BYTES", 5 * 1024 * 1024 * 1024
            ),
            storage_max_bytes=_env_int(
                "NEURON_STORAGE_MAX_BYTES", 20 * 1024 * 1024 * 1024
            ),
            storage_safety_reserve_bytes=_env_int(
                "NEURON_STORAGE_SAFETY_RESERVE_BYTES", 2 * 1024 * 1024 * 1024
            ),
            cpu_limit_percent=_env_float("NEURON_CPU_LIMIT_PERCENT", 25.0),
            daily_egress_bytes=_env_int(
                "NEURON_DAILY_EGRESS_BYTES", 10 * 1024 * 1024 * 1024
            ),
            offline=_env_bool("NEURON_OFFLINE", False),
            prefer_remote=_env_bool("NEURON_PREFER_REMOTE", False),
            peer_refresh_seconds=_env_float("NEURON_PEER_REFRESH_SECONDS", 10.0),
            backup_interval_seconds=_env_float("NEURON_BACKUP_INTERVAL_SECONDS", 60.0),
            request_timeout_seconds=_env_float("NEURON_REQUEST_TIMEOUT_SECONDS", 30.0),
            hot_memory_limit_bytes=_env_int(
                "NEURON_HOT_MEMORY_LIMIT_BYTES", 2 * 1024 * 1024
            ),
            max_request_bytes=_env_int(
                "NEURON_MAX_REQUEST_BYTES", 10 * 1024 * 1024
            ),
            cors_origins=_env_list("NEURON_CORS_ORIGINS"),
        )

    def ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def database_path(self) -> Path:
        return self.data_dir / "neuron.db"

