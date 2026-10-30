# Internet-Scale Neuron-Style Self-Organizing Network for Heterogeneous Multi-Modal LLMs

[简体中文](../../神经元式去中心化大模型网络系统-技术交底书.md) | [English](technical-disclosure.en.md)

> **Translation notice:** This English edition supports international technical review. It is not a legal translation. For patent drafting, claim wording or jurisdiction-specific interpretation, the Chinese source is authoritative.

## 1. Technical background

Existing LLM deployment splits into two broad models:

1. centralized data-center inference, which concentrates compute but creates cost and single points of failure;
2. distributed inference projects that may spread model execution but usually retain centralized coordination, fixed ingress or a narrow set of dedicated GPU workers.

Most consumer CPUs, edge devices and intermittent hosts cannot participate productively, and memory is commonly tied to one provider or one process lifecycle.

NeuronMesh explores a third model: invited heterogeneous hosts form a capability-aware network where any authorized node can act as ingress, model execution may be local, remote or staged, and virtual roles carry durable encrypted memory across replaceable hosts.

## 2. Objective

The system aims to:

- use measured rather than advertised capacity;
- support local small models, remote whole-model providers and compatible pipeline stages;
- preserve explicit online and offline capability boundaries;
- separate long-lived role memory from physical host lifetime;
- replicate encrypted memory across failure domains;
- support evidence-gated continual learning;
- retain a platform-neutral spatial interface;
- preserve audit and failure semantics rather than claiming unlimited self-healing.

## 3. Logical modules

### 3.1 Hardware probing and capacity brokerage

- node identity and signed capability claim;
- device, accelerator, memory, storage and network profile;
- sustained benchmark evidence;
- current slots, thermal/power state and expiry;
- short capacity lease with fencing token.

Hardware specifications are not sufficient evidence of service capacity.

### 3.2 Local and remote inference

- local small-model fallback;
- remote whole-model OpenAI-compatible provider;
- contiguous 2–3-stage Transformer pipeline where justified;
- trusted LAN tensor group;
- typed backend/runtime/model manifests;
- deadline propagation, cancellation and signed receipts.

Public WAN deployment defaults to pipeline parallelism, not unrestricted all-reduce.

### 3.3 Peer discovery and routing

- invited node identity;
- signed capability records with TTL;
- domain catalogs, bootstrap nodes and DHT as later scaling mechanisms;
- request-local planner;
- NAT traversal and relay fallback;
- no mandatory global scheduler.

Routing must satisfy hard compatibility, policy, privacy, deadline and capacity constraints before optimizing latency or cost.

### 3.4 Virtual roles and memory

- role identity separated from host;
- namespace-scoped memory;
- encrypted immutable versions;
- hot/warm/cold tiers;
- replica manifests and failure-domain acknowledgements;
- fence-based role migration;
- tombstone and deletion-debt semantics.

“Persistent” memory is a tested D0–D3 durability contract, not a physical permanence claim.

### 3.5 Continuous learning

- episodic, semantic and procedural memory;
- explicit evidence and consent gate;
- local Adapter training over immutable base models;
- signed update manifests;
- replaceable aggregation;
- regression, safety and poisoning evaluation;
- canary rollout and rollback.

Conversations do not directly mutate global model parameters.

### 3.6 Security and accounting

- node certificates and namespace-scoped user grants;
- signed model/runtime artifacts;
- worker sandbox and quotas;
- idempotent execution, storage and deletion receipts;
- request and quota budgets;
- revocation and policy epochs;
- privacy-safe telemetry.

### 3.7 Spatial adapter

The core exposes a versioned optional adapter for WebXR/OpenXR and engines. Spatial events are untrusted semantic input; avatar output requires a permission broker and action grant.

## 4. End-to-end workflow

1. An invited node establishes identity and publishes signed capability evidence.
2. An ingress receives a request with deadline, privacy, model and budget constraints.
3. Policy is evaluated before candidate resources influence execution.
4. The planner tries local model, remote whole-model provider and then compatible pipeline.
5. Compatible capacity leases are reserved and fenced.
6. Workers execute under immutable model/runtime manifests.
7. Results stream to ingress; step receipts are signed.
8. Memory writes commit locally and receive remote replica acknowledgements according to durability policy.
9. The terminal request state and signed receipts enter accounting/audit.
10. On graceful shutdown, a node drains, freezes admission, replicates high-value state, checkpoints storage and returns a signed receipt.

## 5. Node types are derived views

The system expresses:

- **weak neuron:** ingress, perception, local small model, cache or tolerant asynchronous work;
- **strong neuron:** validated provider for a specific model/task/SLA;
- **group neuron:** trusted high-bandwidth local compute group;
- **domain neuron:** governance and discovery view over a trust domain.

These properties are derived from model compatibility, measured sustained performance, network affinity, energy state and trust evidence. They are not permanent device labels.

## 6. Failure behavior

- expired capability is refreshed or rejected;
- failed stage before first output may be replanned;
- failure after first output is not transparently replayed;
- revoked or fenced workers cannot commit;
- planned shutdown uses drain receipts;
- unexpected power loss is limited to already confirmed storage semantics;
- missing replicas are visible as degraded durability;
- stale tombstones cannot be ignored;
- training updates without evaluation never roll out.

## 7. Research claims

The design must be evaluated against:

- single-node model/offload baselines;
- random, RTT-only and full capability-aware routing;
- WAN pipeline vs remote whole-model provider;
- heterogeneous server/laptop/phone/ARM behavior;
- thermal throttling, battery and network changes;
- planned shutdown and power-loss recovery;
- deletion, stale replica and key-loss scenarios;
- memory quality and token cost;
- adapter quality, regression and training-toxicity tests.

## 8. Boundaries

The project does not initially provide:

- anonymous public participation;
- a universal decentralized global model;
- internet-scale all-reduce;
- production SLA;
- guaranteed physical permanence of memory;
- arbitrary uploaded model code;
- autonomous global training from user interaction.

## 9. Patent-drafting note

Potential novelty should be evaluated around the combination of:

- model/task/SLA-specific capacity derivation;
- request-local planning with short capacity leases and fencing;
- whole-model versus pipeline selection;
- host-independent role memory with failure-domain-aware durability;
- evidence-gated local adapter updates and rollback.

No novelty or patentability conclusion is made here. The Chinese technical source and formal prior-art search control any legal process.
