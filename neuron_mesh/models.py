from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ResourcePledge(BaseModel):
    storage_min_bytes: int = Field(ge=0)
    storage_max_bytes: int = Field(ge=0)
    storage_safety_reserve_bytes: int = Field(ge=0)
    cpu_limit_percent: float = Field(ge=1, le=100)
    daily_egress_bytes: int = Field(ge=0)
    availability_class: Literal[
        "resident", "resident-constrained", "opportunistic", "archive-only"
    ]

    @field_validator("storage_max_bytes")
    @classmethod
    def validate_storage_max(cls, value: int, info: Any) -> int:
        minimum = info.data.get("storage_min_bytes", 0)
        if value < minimum:
            raise ValueError("storage_max_bytes must be >= storage_min_bytes")
        return value


class ComputeProfile(BaseModel):
    cpu_count: int
    cpu_model: str
    ram_total_bytes: int
    ram_available_bytes: int
    gpu_name: str | None = None
    gpu_memory_bytes: int | None = None
    backend: str = "cpu"
    synthetic_ops_per_second: float = 0.0


class NetworkProfile(BaseModel):
    public_url: str
    failure_domain: str
    link_class: str = "unknown"
    rtt_p95_ms: float | None = None
    uplink_mbps_p10: float | None = None
    metered: bool = False


class DerivedCapacity(BaseModel):
    tier: Literal["strong", "weak"]
    for_model: str
    task_profile: str
    valid_until: float


class NodeCapability(BaseModel):
    protocol: str = "neuron.node/0.1"
    node_id: str
    node_name: str
    device_class: str
    unit_scope: Literal["single", "group", "domain"] = "single"
    service_roles: list[str]
    models: list[str]
    resource_pledge: ResourcePledge
    compute: ComputeProfile
    network: NetworkProfile
    storage_used_bytes: int
    storage_capacity_bytes: int
    admitted: bool
    admission_reasons: list[str] = Field(default_factory=list)
    derived_capacity: list[DerivedCapacity]
    observed_at: float
    resident_state: Literal[
        "joined", "warming", "resident", "draining", "hibernated", "recovering"
    ] = "resident"


class PeerAnnouncement(BaseModel):
    capability: NodeCapability
    public_key_b64: str
    signature_b64: str


class PeerView(BaseModel):
    node_id: str
    name: str
    public_url: str
    failure_domain: str
    capability: NodeCapability
    public_key_b64: str
    signature_b64: str
    last_seen: str
    rtt_ms: float | None = None
    online: bool = True


MemoryKind = Literal["event", "fact", "preference", "procedure", "summary"]
MemoryStatus = Literal["active", "sealed", "tombstoned"]
MemoryTier = Literal["hot", "warm", "cold"]


class MemoryWriteRequest(BaseModel):
    namespace_id: str
    owner_id: str
    role_id: str | None = None
    kind: MemoryKind = "event"
    text: str = Field(min_length=1, max_length=1_000_000)
    summary: str = ""
    source_refs: list[str] = Field(default_factory=list)
    importance: int = Field(default=3, ge=1, le=5)
    ttl_seconds: int | None = Field(default=None, ge=1)


class MemoryView(BaseModel):
    memory_id: str
    namespace_id: str
    owner_id: str
    role_id: str | None
    kind: MemoryKind
    text: str | None = None
    summary: str | None = None
    content_hash: str
    source_refs: list[str]
    importance: int
    status: MemoryStatus
    tier: MemoryTier
    version: int
    size_bytes: int
    created_at: str
    updated_at: str
    durability: Literal["D0", "D1", "D2", "D3"]
    replicas: list[str] = Field(default_factory=list)
    local_content: bool = True


class RoleCreateRequest(BaseModel):
    role_id: str
    owner_id: str
    namespace_id: str
    display_name: str = ""
    avatar_bindings: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(
        default_factory=lambda: ["speak", "gaze", "gesture"]
    )


class RoleView(RoleCreateRequest):
    primary_host_id: str
    state_version: int = 1
    status: Literal[
        "active", "draining", "migrating", "hibernated", "recovering", "retired"
    ] = "active"
    created_at: str = ""
    updated_at: str = ""


class SpatialSessionOpen(BaseModel):
    role_id: str
    owner_id: str
    space_id: str
    frame_id: str = "world"
    privacy_mode: Literal["local_only", "redacted_features", "explicit_media"] = (
        "redacted_features"
    )


class SpatialEvent(BaseModel):
    source: Literal[
        "headset",
        "phone",
        "camera",
        "microphone",
        "scene",
        "controller",
        "text",
    ]
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    frame_id: str = "world"
    ttl_ms: int = Field(default=1000, ge=1, le=60_000)
    untrusted: bool = True


class AvatarIntentRequest(BaseModel):
    action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    permission_token: str | None = None


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool", "developer"]
    content: str | list[dict[str, Any]]
    name: str | None = None

    model_config = ConfigDict(extra="allow")


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = Field(default=None, ge=1)

    model_config = ConfigDict(extra="allow")


class BackupStoreRequest(BaseModel):
    memory_id: str
    namespace_id: str
    owner_id: str
    content_hash: str
    cipher_b64: str
    nonce_b64: str
    key_id: str
    size_bytes: int
    source_node_id: str
    source_failure_domain: str
    created_at: str


class BackupFetchResponse(BaseModel):
    memory_id: str
    namespace_id: str
    owner_id: str
    content_hash: str
    cipher_b64: str
    nonce_b64: str
    key_id: str
    size_bytes: int


class ShutdownReceipt(BaseModel):
    node_id: str
    memory_count: int
    replicated_memory_count: int
    degraded_memory_count: int
    replica_count: int
    memory_ids_root: str
    status: Literal["hardened", "local_only", "degraded"]
    created_at: str
    signature_b64: str


class RoleMigrationRequest(BaseModel):
    target_node_id: str = Field(min_length=8, max_length=128)
    transfer_secret: str = Field(min_length=16, max_length=1024)


class RoleMigrationPackage(BaseModel):
    format: str = "neuron.role-migration/0.1"
    role_id: str
    source_node_id: str
    target_node_id: str
    salt_b64: str
    nonce_b64: str
    cipher_b64: str
    created_at: str


class RoleMigrationImport(BaseModel):
    transfer_secret: str = Field(min_length=16, max_length=1024)
    package: RoleMigrationPackage


class RoleMigrationResult(BaseModel):
    role: RoleView
    imported_memory_count: int
    source_node_id: str
    target_node_id: str

