from __future__ import annotations

import hashlib
import platform
import shutil
import subprocess
import time

import psutil

from .config import Settings
from .models import (
    ComputeProfile,
    DerivedCapacity,
    NetworkProfile,
    NodeCapability,
    ResourcePledge,
)
from .security import NodeIdentity


class CapabilityService:
    def __init__(self, settings: Settings, identity: NodeIdentity) -> None:
        self.settings = settings
        self.identity = identity

    def _gpu(self) -> tuple[str | None, int | None, str]:
        executable = shutil.which("nvidia-smi")
        if executable:
            try:
                result = subprocess.run(
                    [
                        executable,
                        "--query-gpu=name,memory.total",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=3,
                )
                first = next(
                    (line.strip() for line in result.stdout.splitlines() if line.strip()),
                    None,
                )
                if first:
                    name, memory_mib = [part.strip() for part in first.rsplit(",", 1)]
                    return name, int(float(memory_mib)) * 1024 * 1024, "cuda"
            except (OSError, subprocess.SubprocessError, ValueError):
                pass

        if platform.system() == "Darwin" and platform.machine() == "arm64":
            return "Apple Silicon GPU", None, "metal"
        return None, None, "cpu"

    @staticmethod
    def _synthetic_benchmark() -> float:
        started = time.perf_counter()
        digest = b"neuron-mesh"
        iterations = 120_000
        for _ in range(iterations):
            digest = hashlib.sha256(digest).digest()
        elapsed = max(time.perf_counter() - started, 1e-9)
        return iterations / elapsed

    def pledge(self) -> ResourcePledge:
        return ResourcePledge(
            storage_min_bytes=self.settings.storage_pledge_bytes,
            storage_max_bytes=self.settings.storage_max_bytes,
            storage_safety_reserve_bytes=self.settings.storage_safety_reserve_bytes,
            cpu_limit_percent=self.settings.cpu_limit_percent,
            daily_egress_bytes=self.settings.daily_egress_bytes,
            availability_class=self.settings.availability_class,
        )

    def current(self, resident_state: str = "resident") -> NodeCapability:
        memory = psutil.virtual_memory()
        usage = psutil.disk_usage(str(self.settings.data_dir))
        gpu_name, gpu_memory, backend = self._gpu()
        reasons: list[str] = []
        storage_after_reserve = max(
            0, usage.free - self.settings.storage_safety_reserve_bytes
        )
        if self.settings.storage_max_bytes < self.settings.storage_pledge_bytes:
            reasons.append("storage_max_bytes is below the required storage pledge")
        if storage_after_reserve < self.settings.storage_pledge_bytes:
            reasons.append("insufficient free disk after the safety reserve")
        if self.settings.cpu_limit_percent <= 0:
            reasons.append("CPU contribution must be greater than zero")
        commitment = min(
            self.settings.storage_pledge_bytes,
            storage_after_reserve,
            self.settings.storage_max_bytes,
        )
        compute = ComputeProfile(
            cpu_count=psutil.cpu_count(logical=True) or 1,
            cpu_model=platform.processor() or platform.machine() or "unknown",
            ram_total_bytes=memory.total,
            ram_available_bytes=memory.available,
            gpu_name=gpu_name,
            gpu_memory_bytes=gpu_memory,
            backend=backend,
            synthetic_ops_per_second=self._synthetic_benchmark(),
        )
        admitted = not reasons
        strong = admitted and (
            backend in {"cuda", "metal", "rocm"}
            or (compute.ram_total_bytes >= 64 * 1024**3 and compute.cpu_count >= 12)
        )
        tier = "strong" if strong else "weak"
        effective_roles = (
            self.settings.service_roles if admitted else ["ingress"]
        )
        return NodeCapability(
            node_id=self.identity.node_id,
            node_name=self.settings.node_name,
            device_class=self.settings.device_class,
            service_roles=effective_roles,
            models=[self.settings.model_id],
            resource_pledge=ResourcePledge(
                storage_min_bytes=commitment,
                storage_max_bytes=max(
                    self.settings.storage_pledge_bytes,
                    self.settings.storage_max_bytes,
                ),
                storage_safety_reserve_bytes=self.settings.storage_safety_reserve_bytes,
                cpu_limit_percent=self.settings.cpu_limit_percent,
                daily_egress_bytes=self.settings.daily_egress_bytes,
                availability_class=self.settings.availability_class,
            ),
            compute=compute,
            network=NetworkProfile(
                public_url=self.settings.public_url,
                failure_domain=self.settings.failure_domain,
            ),
            storage_used_bytes=usage.used,
            storage_capacity_bytes=usage.total,
            admitted=admitted,
            admission_reasons=reasons,
            derived_capacity=[
                DerivedCapacity(
                    tier=tier,
                    for_model=self.settings.model_id,
                    task_profile="backend-service",
                    valid_until=time.time() + 300,
                )
            ],
            observed_at=time.time(),
            resident_state=resident_state if admitted else "warming",
        )

    def signed(self, resident_state: str = "resident") -> dict[str, object]:
        capability = self.current(resident_state)
        payload = capability.model_dump(mode="json")
        return {
            "capability": payload,
            "public_key_b64": self.identity.public_key_b64,
            "signature_b64": self.identity.sign(payload),
        }

    def disk_free_bytes(self) -> int:
        return int(psutil.disk_usage(str(self.settings.data_dir)).free)

