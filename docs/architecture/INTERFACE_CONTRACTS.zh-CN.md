# 协议与接口契约

[English](INTERFACE_CONTRACTS.md) | [简体中文](INTERFACE_CONTRACTS.zh-CN.md)

**状态：** 架构契约草案 `v0.1`  
**目的：** 定义入口、规划器、Worker、注册表、记忆托管、角色控制器和空间适配器共享的最小版本化对象

本文是实现要求，不表示当前 API 已有全部字段。JSON Schema 生成、一致性夹具和兼容测试属于 Gate A 交付物。

## 1. 契约规则

- 每个对象包含 `schema`、`version`、`id`、`created_at` 和签发者身份。
- ID 不透明、有长度上限且区分大小写；公开 ID 不嵌入用户数据。
- 安全相关时间使用 UTC 并包含过期时间。
- 未知关键字段导致拒绝。
- 只有标记为非关键的可选字段才可以安全忽略。
- 每个跨节点变更通过显式幂等键保证幂等。
- 签名覆盖对象声明的规范化序列化。
- 默认契约不包含 Bearer Token、私钥、记忆明文或原始媒体。
- 存储格式和执行计划固定不可变 Schema/产物摘要。

## 2. 通用 Envelope

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

`audience` 防止签名对象被重放到无关服务。交互请求可通过幂等键、有限期限和 fencing 代替持久 nonce 表。

## 3. 核心对象

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

承诺是边界，不是当前空闲容量证明。

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

静态声明与动态观测分离。当前队列、温度和空闲 slot 属于 `CapacityLease/v1`，不属于长期能力记录。

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

模型 ID 面向人类，执行绑定摘要元组。

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

连续覆盖、无重叠和精确模型上下文兼容是强制条件。

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

计划在预留后不可变。重新规划生成新版本。

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

大型/私有输入通过授权对象 ID 引用，不强制将明文放入控制面日志。

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

没有匹配租约和 fence，计划不能启动。

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

回执不包含 Prompt 或激活明文。

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

情景、语义、偏好和程序记忆可使用同一容器，但准入和晋升策略不同。

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

仅副本数量不够，必须有故障域和摘要证据。

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

角色身份独立于主节点。

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

空间契约是可选适配器，不能成为记忆或推理核心依赖。

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

自报指标是声明，不是评估结果。

### 3.15 `CoordinationTask/v1`

参考实现把该对象持久化到 SQLite，并通过 `/v1/tasks` 暴露。其
`execution_mode` 明确标记为 `coordination`，因为当前契约尚不包含真实模型阶段执行。

```text
task_id
objective
requester_host_id
target_hosts: 1..40
participant_count
max_parallel: 1..20
requested_tflops / granted_tflops
execution_mode: coordination
status: pending | running | complete | failed
created_at / service_start_at / completed_at
assignments[]:
  assignment_id / sequence
  stage_name / stage_weight / capability
  host_id / host_name
  status: pending | active | done | failed
  share_percent / allocated_tflops
  service_seconds / started_at / ends_at / completed_at
```

分配项是按能力寻址的 Worker 槽位。任务可以覆盖多台主机，但同一时刻活动的
分配项不会超过 `max_parallel`。每个活动分配项拥有独立截止时间；完成后释放
一个槽位，并允许一个 pending 分配项补位。关系图不绘制永久的任务到 Worker
连线，只为每次入口请求或 Worker 调用绘制短时活动脉冲。

## 4. 传输映射

### 4.1 阶段 1：可信 HTTP/TLS 参考路径

受控研究允许：

- HTTPS/mTLS 控制与请求传输；
- JSON 控制对象；
- SSE 流式响应；
- 签名清单和回执；
- 租户短期 Bearer Token；
- 不直接暴露 Worker RPC。

### 4.2 目标：认证 QUIC/libp2p

| 通道 | 传输 | 语义 |
| --- | --- | --- |
| 成员与目录 | 认证请求流 | 带 epoch/TTL 的快照 |
| 容量租约 | 请求流 | 幂等预留 |
| 完整模型请求 | 双向流 | 类似 HTTP 的请求/响应 |
| 阶段控制 | 控制流 | 计划、fence、deadline 和取消 |
| 激活传输 | 类型化数据流 | 精确 shape/dtype 摘要和背压 |
| 结果流 | 到入口的直接流 | 有序 token 和终态回执 |
| 记忆对象 | 分块请求流 | 摘要寻址密文 |
| 训练更新 | 有界产物流 | 可恢复、内容寻址 |

具体 libp2p protocol ID 只有在一致性测试后才冻结。

## 5. 错误模型

| 类别 | 重试边界 | 含义 |
| --- | --- | --- |
| `auth_denied` | 无新授权不重试 | 身份或策略失败 |
| `lease_unavailable` | 执行前 | 无兼容容量 |
| `lease_expired` | 提交前 | 容量过期 |
| `fenced` | 旧 epoch 永不重试 | 存在更新所有者 |
| `manifest_incompatible` | 否 | 模型/运行时/shape 不匹配 |
| `deadline_exceeded` | 不可逆输出前 | 预算耗尽 |
| `worker_failed` | 不可逆输出前 | 执行失败 |
| `stream_interrupted` | 客户端决定 | 已输出，流中断 |
| `quota_exceeded` | 新显式预算 | 租户/运维上限 |
| `storage_degraded` | 按耐久策略 | 所需副本未确认 |
| `deletion_incomplete` | 修复任务 | 已知副本未确认删除 |
| `evaluation_failed` | 新训练轮次 | 更新不可发布 |

错误响应包含计划/策略 epoch、安全重试边界和回执 ID，不泄漏内部密钥或其他命名空间存在性。

## 6. 兼容与迁移

- Capability 和 Manifest 读取器只接受明确支持的 major version。
- 语义变化需要新 major schema。
- 新增字段需要默认值及兼容夹具。
- 未知关键扩展导致反序列化拒绝。
- 存储迁移为幂等、可恢复作业，带前后校验和。
- API 弃用有观察窗口和活跃用户遥测。
- 不允许削弱认证、加密或耐久性的自动降级。

## 7. 必需一致性夹具

Gate A 必须包含：

1. 有效/无效签名和重放；
2. 过期 capability、策略和租约；
3. 阶段缺口、重叠、Tokenizer 不匹配和激活 dtype 不匹配；
4. 重复请求投递；
5. 租约过期和陈旧 fence；
6. 未知关键扩展；
7. 记忆摘要不匹配和缺少故障域确认；
8. 墓碑对陈旧副本；
9. 角色迁移每个状态边界；
10. 训练更新缺少评估或回滚产物；
11. 超大和深层嵌套输入；
12. 恶意 Peer URL 和重定向。

## 8. 接口所有权

| 接口 | 建议所有者 |
| --- | --- |
| 节点身份与成员 | 信任/身份工作组 |
| Capability 与 Lease | 调度/传输工作组 |
| Model/Stage Manifest | 运行时与模型服务工作组 |
| Request 与 Receipt | API 与可观测性工作组 |
| Memory/Role | 持久状态工作组 |
| Training Round/Update | 学习工作组 |
| Spatial Session | 空间适配器工作组 |

接口变更需要受影响所有者、兼容夹具和迁移说明，防止单一实现包成为意外协议权威。
