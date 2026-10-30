# Protocol and Interface Contracts

[English](INTERFACE_CONTRACTS.md) | [简体中文](INTERFACE_CONTRACTS.zh-CN.md)

**Status:** Draft architecture contract `v0.1`  
**Purpose:** Define the minimum versioned objects shared across ingress, planner, workers, registries, memory custodians, role controllers and spatial adapters

These contracts are design requirements for implementation. They are not a promise that all fields exist in the current API. JSON Schema generation, conformance fixtures and compatibility tests are Gate A deliverables.

## 1. Contract rules

- Every object has `schema`, `version`, `id`, `created_at` and issuer identity.
- IDs are opaque, bounded and case-sensitive. User data is not embedded in public IDs.
- Security-relevant timestamps use UTC and include expiry.
- Unknown critical fields cause rejection.
- Optional fields are safe to ignore only when marked non-critical.
- Every cross-node mutation is idempotent through an explicit key.
- Signatures cover a canonical serialization of the declared object.
- No contract contains a bearer token, private key, plaintext memory or raw media by default.
- Storage formats and execution plans pin immutable schema/artifact digests.

## 2. Common envelope

```json
{
  "schema": "neuron.request/v1",
  "version": 1,
  "id": "opaque-global-id",
  "created_at": "2026-10-30T10:00:00Z",
  "issuer": "node:sha256:...",
  "audience": "domain:...",
  "idempotency_key": "opaque-retry-key",
  "expires_at": "2026-10-30T10:05:00Z",
  "critical_extensions": [],
  "extensions": {},
  "signature_b64": "..."
}
```

`audience` prevents a signed object from being replayed to an unrelated service. For interactive requests, nonce/replay state can be replaced by the idempotency key plus bounded expiry and fencing.

## 3. Core objects

### 3.1 `HardwarePledge/v1`

```text
node_id
architecture / device_class
cpu_budget
ram_budget
accelerator_budget
storage_commitment
egress_budget
availability_class
allowed_time_windows
power_and_thermal_constraints
valid_from / valid_until
operator_signature
```

The pledge is a commitment boundary, not proof of current free capacity.

### 3.2 `NodeCapability/v1`

```text
node_identity
membership_epoch
capability_epoch
supported_transports
service_roles
runtime_backends
installed_model_manifests
benchmark_evidence
network_affinity_observations
resource_pledge_digest
observed_at / valid_until
node_signature
```

Static claims and dynamic observations are separate. Current queue, temperature and free slots belong to a `CapacityLease/v1`, not a long-lived capability record.

### 3.3 `ModelManifest/v1`

```text
model_id / revision
architecture
parameter_count
license_id / policy_notes
weight_artifact_digests
tokenizer_digest
chat_template_digest
attention_and_rope_config_digest
quantization_and_precision
context_limit
runtime_compatibility
stage_boundary_schema
artifact_signers / trust_evidence
```

The model ID is human-facing. The digest tuple is what execution binds to.

### 3.4 `StageManifest/v1`

```text
model_manifest_digest
stage_id
layer_start / layer_end
input_contract_digest
output_contract_digest
activation_dtype_and_shape
kv_cache_policy
estimated_memory
runtime_image_digest
operator_implementation_digest
supported_batching
health_probe
```

Contiguous coverage, no overlap and exact model-context compatibility are mandatory.

### 3.5 `ExecutionPlan/v1`

```text
plan_id / request_id
mode: local-small | remote-whole-model | trusted-group | pipeline | async-batch
policy_epoch
ordered stages or provider
model/runtime digests
capacity_lease_ids
deadline / total_budget
activation_transport
result_transport
retry_boundary
failure_domains
privacy_scope
accounting_tags
ingress_signature
```

A plan is immutable after reservation. Replanning emits a new plan version.

### 3.6 `RequestEnvelope/v1`

```text
tenant_id_hash
agent_or_user_grant
operation
normalized_input_digest
input_object_references
model_requirement
privacy_mode
deadline
quality_floor
output_mode: non-stream | stream | async
context_token_budget
output_token_budget
idempotency_key
retention_policy
```

The envelope references large/private inputs by authorized object ID. It does not force plaintext into control-plane logs.

### 3.7 `CapacityLease/v1`

```text
lease_id / plan_id / request_id
provider_node / group / worker
compatibility_digest
slot_count
queue_position
start_by / expires_at
max_work
policy_epoch
privacy_and_license_scope
revocation_conditions
fencing_token
provider_signature
```

The plan cannot start without matching leases and fences.

### 3.8 `StepReceipt/v1`

```text
receipt_id / request_id / plan_id
step_id / worker_id
lease_id / fence
model_and_runtime_digests
input_digest / output_digest
started_at / completed_at
resource_usage
bytes_in / bytes_out
result_class
failure_class
worker_signature
```

Receipts do not contain prompt or activation plaintext.

### 3.9 `MemoryObject/v1`

```text
object_id
namespace_id
owner_scope
logical_type
version_vector_or_parent_version
sensitivity_class
retention_policy
consent_or_write_grant
encrypted_content_manifest
blind_index_manifest
created_at / supersedes
```

Episodic, semantic, preference and procedural memory may use the same container but different admission and promotion policies.

### 3.10 `ReplicaManifest/v1`

```text
object_id / version_digest
required_durability
entries[
  custodian_id
  failure_domain
  encrypted_chunk_digests
  version
  acknowledged_at
  receipt_id
]
repair_state
last_scrub
deletion_epoch
manifest_epoch
authority_signature
```

Replica count alone is insufficient; failure-domain and digest evidence are required.

### 3.11 `RoleManifest/v1`

```text
role_id
owner_id_hash
namespace_grants
model_and_adapter_manifests
allowed_tools_and_actions
memory_scope
primary_host
primary_epoch
lease_id
capability_requirements
migration_policy
created_at / updated_at
role_controller_signature
```

The role identity is independent of the primary host.

### 3.12 `SpatialSession/v1`

```text
session_id / role_id / space_id
adapter_and_protocol_version
declared_frames
privacy_mode
event_order_constraints
expiry
action_grants
bystander_privacy_policy
```

Spatial contracts are optional adapters. They cannot become a dependency of memory or inference core.

### 3.13 `TrainingRound/v1`

```text
round_id
hypothesis
base_model_manifest_digest
eligible_participants
data_and_consent_scope
update_schema_and_rank
aggregation_algorithm
evaluation_suite_digest
poisoning_and_privacy_policy
canary_and_rollback_plan
coordinator_signature
```

### 3.14 `AdapterUpdate/v1`

```text
round_id / participant_pseudonym
base_model_digest
training_manifest_digest
update_artifact_digest
update_signature
resource_receipt_id
declared_metrics
```

Self-declared metrics are claims, not evaluation results.

## 4. Transport mapping

### 4.1 Phase 1: trusted HTTP/TLS reference path

Allowed for controlled research:

- HTTPS/mTLS for control and request transport;
- JSON objects for control;
- SSE for streaming responses;
- signed manifests and receipts;
- short-lived bearer tokens for tenant access;
- no direct exposure of worker RPC ports.

### 4.2 Target: authenticated QUIC/libp2p path

| Channel | Transport | Semantics |
| --- | --- | --- |
| Membership and catalog | authenticated request stream | snapshot with epoch/TTL |
| Capacity lease | request stream | idempotent reservation |
| Whole-model request | bidirectional stream | normal HTTP-like request/response |
| Stage control | control stream | plan, fence, deadline and cancellation |
| Activation transfer | typed data stream | exact shape/dtype digest and backpressure |
| Result stream | direct stream to ingress | ordered tokens and terminal receipt |
| Memory objects | chunked request stream | digest-addressed encrypted blobs |
| Training updates | bounded artifact transfer | resumable, content-addressed |

The exact libp2p protocol IDs are reserved only after conformance tests.

## 5. Error model

Every cross-node error has a stable class:

| Class | Retry boundary | Meaning |
| --- | --- | --- |
| `auth_denied` | Never without new grant | Identity or policy failure |
| `lease_unavailable` | Before execution | No compatible capacity |
| `lease_expired` | Before commit | Capacity expired |
| `fenced` | Never with old epoch | Newer owner exists |
| `manifest_incompatible` | No | Model/runtime/shape mismatch |
| `deadline_exceeded` | Before irreversible output | Budget exhausted |
| `worker_failed` | Before irreversible output | Execution failed |
| `stream_interrupted` | Client decision | Output began, stream ended |
| `quota_exceeded` | New explicit budget | Tenant/operator limit |
| `storage_degraded` | Per durability policy | Required copies not confirmed |
| `deletion_incomplete` | Repair job | Known replicas not acknowledged deletion |
| `evaluation_failed` | New training round | Update not eligible for rollout |

An error response includes the plan/policy epoch, safe retry boundary and receipt IDs. It must not leak internal secrets or another namespace's existence.

## 6. Compatibility and migration

- Capability and manifest readers accept only explicitly supported major versions.
- Semantic changes require a new schema major version.
- Additive fields require a default and compatibility fixture.
- Deserializers reject unknown critical extensions.
- Storage migration is an idempotent, resumable job with before/after checksums.
- API deprecation has a documented observation window and telemetry to find active users.
- No automatic downgrade that weakens authentication, encryption or durability.

## 7. Required conformance fixtures

Gate A must include:

1. valid/invalid signatures and replay;
2. expired capability, policy and lease;
3. stage gap, overlap, tokenizer mismatch and activation dtype mismatch;
4. duplicate request delivery;
5. lease expiry and stale fence;
6. unknown critical extension;
7. memory digest mismatch and missing failure-domain ack;
8. tombstone versus stale replica;
9. role migration at every state boundary;
10. training update missing evaluation or rollback artifact;
11. oversized/deeply nested inputs;
12. malicious peer URL and redirect behavior.

## 8. Interface ownership

| Interface | Proposed owner |
| --- | --- |
| Node identity and membership | Trust/identity working group |
| Capability and lease schema | Scheduling/transport working group |
| Model/stage manifest | Runtime and model-serving working group |
| Request and receipt schema | API and observability working group |
| Memory/role schema | Durable-state working group |
| Training round/update schema | Learning working group |
| Spatial session | Spatial adapter working group |

Any interface change requires the affected owner, compatibility fixture and migration note. This prevents a single implementation package from becoming the accidental protocol authority.
