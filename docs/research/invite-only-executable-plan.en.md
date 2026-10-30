# NeuronMesh: Executable Research Plan for an Invite-Only Network

[简体中文](../../神经元式去中心化大模型网络系统-研究型邀请制可执行方案.md) | [English](invite-only-executable-plan.en.md)

**English edition note:** This is the international technical edition of the Chinese research plan. It preserves the architecture, constraints, experiment design and stop criteria; the Chinese source contains additional supporting detail.

## 1. Executive conclusion

An invite-only heterogeneous AI network is feasible as a research programme. The feasible proposition is not “any device instantly becomes a production AI cluster.” It is:

- authorized nodes contribute measured, typed capacity;
- any authorized node can act as ingress;
- execution is planned locally under policy and deadline constraints;
- model execution may use local small models, remote whole-model providers or a limited pipeline;
- durable memory and roles are independent of one host;
- every availability, privacy, durability and learning claim has a reproducible failure boundary.

The first target is a reproducible 2–12-node invited testbed, not anonymous internet scale.

## 2. Required technical corrections

### 2.1 QUIC does not require an additional Noise layer

libp2p QUIC uses QUIC/TLS 1.3 transport security. Noise may be relevant to non-encrypted TCP transports, but “QUIC + Noise” is not an automatic requirement. Application-level task encryption may still be needed for end-to-end data protection across intermediaries.

### 2.2 GGUF is not a distributed-stage protocol

GGUF is a local model container. A pipeline needs an immutable stage manifest containing model revision, tokenizer, template, layer range, precision, artifact and runtime digests.

### 2.3 Direct result return

The final stage should stream back to ingress over the best available authenticated path. Results need not travel backward through every control hop.

### 2.4 Public internet is not a tensor-parallel fabric

Tensor parallelism creates frequent collective communication. Use it only inside a tightly coupled LAN/RDMA group. Public WAN experiments should initially use pipeline parallelism with two or three stages.

### 2.5 The network does not guarantee a permanent node

“Join and stay resident” is an operator commitment and lifecycle policy, not physics. Planned shutdown, revocation, power loss and maintenance require explicit drain and durability semantics.

## 3. Target planes

### 3.1 Membership and trust

- invitation authority and domain membership;
- node identity certificate;
- model/runtime role permissions;
- revocation, expiry and rotation;
- tenant and namespace grants.

### 3.2 Discovery and planning

- signed static capability records with TTL;
- short capacity leases for current slots;
- hierarchical domain catalogs and later DHT;
- request-local planning;
- direct link observations;
- bounded relay and bootstrap services.

### 3.3 Inference data plane

- OpenAI-compatible ingress;
- local small model;
- remote whole-model provider;
- pipeline stage workers;
- activation transport with shape/dtype manifests;
- streaming result path;
- cancellation, deadlines and signed step receipts.

### 3.4 Durable state and learning

- namespace memory authority;
- immutable object versions and replica manifests;
- virtual-role manifests and primary epochs;
- evidence-gated adapter experiments;
- deletion, retention and audit evidence.

### 3.5 Observability

- request and plan IDs;
- policy/capability epochs;
- queue, TTFT, inter-token latency and transfer;
- lease/fence and terminal state;
- failure class and safe retry boundary;
- resource use without prompt or memory plaintext.

## 4. Node roles

| Role | Minimum shape | Responsibility | Default prohibition |
| --- | --- | --- | --- |
| `ingress` | Stable network, 2 CPU, 4 GB RAM | API, auth, request spec, routing, streaming | Large model stage |
| `perception` | CPU/optional accelerator | OCR, ASR, VAD, image encoding, quality checks | Required for every request |
| `pipeline-worker` | Enough memory for a defined stage | Fixed contiguous layer execution | Arbitrary uploaded code |
| `tensor-group` | Trusted high-bandwidth LAN/RDMA | Tensor parallel or prefill/decode separation | WAN all-reduce |
| `relay` | Stable public reachability | Bounded NAT fallback | Plaintext inspection or unlimited forwarding |
| `light-edge` | Phone, set-top box, ARM SBC | Ingress, local model, perception, cache | Critical long-running stage |

A physical host may advertise multiple roles. Each role needs a passed benchmark or manifest compatibility check.

## 5. Capability record

A capability record contains:

- node and membership identity;
- device and runtime architecture;
- supported transports;
- service roles;
- model and stage manifests;
- sustained benchmark evidence;
- network observations;
- energy and availability constraints;
- capability epoch and expiry;
- node signature.

Current free slots, queue, temperature, battery and active leases are dynamic state and must not be merged into a long-lived signed capability.

## 6. Model and stage manifests

A compatible pipeline binds:

```text
model_id and model_revision
license_id
tokenizer hash
chat template hash
attention/RoPE configuration
layer start/end
precision and activation dtype
artifact hash
runtime image digest
maximum context
estimated memory
```

Any missing or mismatched critical field rejects the plan. A pipeline must cover contiguous layers with no gap or overlap.

## 7. Device, compute, network and energy profiles

Device labels choose installation packages, not execution capacity. Scheduling requires:

1. device profile;
2. accelerator, runtime and model format;
3. sustained throughput after thermal stabilization;
4. RAM/VRAM headroom;
5. network RTT, jitter, loss, throughput and metering;
6. power source and allowed time window;
7. trust and license scope.

### 7.1 Network affinity

| Level | Approximate meaning | Suitable work |
| --- | --- | --- |
| L0 | Same device/process | Private and minimal-latency work |
| L1 | Stable LAN, typically <20 ms P95 RTT | Interactive pipeline, tensor group, hot failover |
| L2 | Metro/nearby network, 20–60 ms | 2–3-stage interactive pipeline |
| L3 | Regional, 60–150 ms | Whole-model, prefill, asynchronous work |
| L4 | Remote/high-jitter/relay | Batch, replication, model distribution |

Thresholds are initial configuration and must be re-established by workload benchmarks. Exact coordinates or SSIDs should not be collected for distance.

## 8. Weak, strong, group and domain neurons

These are orthogonal views:

- `unit_scope`: `single`, `group`, `domain`;
- `capacity_tier`: `strong` or `weak` for a specific model/task/SLA;
- `service_roles`: current concrete responsibilities.

### 8.1 Weak neuron

Useful for ingress, auth, request shaping, OCR/ASR, caching, small local models and tolerant asynchronous jobs. It enters a critical pipeline only after passing the stage benchmark.

### 8.2 Strong neuron

Can serve a whole model or a high-value stage after warm-up and sustained throughput validation. The same GPU may be strong for a 3B model and weak for a large pipeline.

### 8.3 Group neuron

A logical high-bandwidth group with a signed member/topology epoch. Group capacity cannot be calculated by simply summing member peak FLOPS; it must be benchmarked.

### 8.4 Domain neuron

A governance and discovery view, not one giant computer. It publishes available roles and policy scopes but does not own every namespace or become the mandatory request scheduler.

### 8.5 Dynamic promotion

- demote immediately on hard failure;
- promote only after repeated benchmark windows;
- evaluate roles per model/task;
- use hysteresis;
- record model, benchmark, throughput, temperature, power and lease evidence.

## 9. Hardware node and virtual role

A host contributes a hardware/resource pledge. A virtual role is a separate manifest containing:

- role identity and owner;
- namespace grants;
- model/adapter references;
- allowed tools/actions;
- memory scope;
- capability requirements;
- primary host and fenced epoch;
- migration and recovery policy.

Memory follows the role/namespace, not the host filesystem.

## 10. Request execution

1. Ingress creates request ID, idempotency key, deadline and privacy mode.
2. Authentication, size limits, content policy and budget are checked.
3. Planner evaluates local model and remote whole-model candidates.
4. It constructs a pipeline only if a single provider cannot satisfy the request.
5. Compatible capacity leases are reserved.
6. The execution plan is bound to artifacts, policy epoch, deadline and fence.
7. Workers execute and sign step receipts.
8. Results stream directly to ingress.
9. The terminal state enters accounting and audit.

### 10.1 Planner

Minimize predicted:

```text
TTFT + queue + transfer + failure penalty + cross-domain / energy / cost
```

Subject to:

- stage completeness and artifact compatibility;
- memory headroom;
- deadline feasibility;
- privacy, region and license;
- invitation/revocation state;
- current capacity lease;
- tenant and provider quotas.

### 10.2 Whole model vs pipeline

1. If local small model meets quality, privacy and deadline, run locally.
2. If one remote provider can hold and serve the whole model, prefer it.
3. If no node can hold the model, consider a nearby 2–3-stage pipeline.
4. If the deadline allows, submit asynchronous/batch work.
5. Otherwise reject or explicitly downgrade quality.

## 11. Online and offline modes

### 11.1 Online

Available capability is the intersection of:

```text
all network members
∩ role/tenant policy
∩ model/runtime/stage compatibility
∩ privacy and geography
∩ current online capacity lease
∩ quota
∩ a deadline-feasible path
```

It is not permission to monopolize all hosts or run every model.

### 11.2 Offline

Use only:

- local model or cached stage;
- local perception;
- local memory cache and index;
- approved local adapters;
- local tools and WAL changes.

The UI must state which remote capabilities disappeared.

### 11.3 Reconnection

1. Obtain current membership and policy epoch.
2. Compare local journal/replica state.
3. Upload pending changes with idempotency.
4. Resolve conflicts.
5. Apply monotonic tombstones.
6. Refresh indexes and model/runtime state.
7. Re-enter `resident` only after required replicas are confirmed.

Important facts use version vectors or owner confirmation, not blind last-write-wins.

## 12. Runtime boundaries

### 12.1 Pipeline activation volume

Approximate per-token boundary bytes:

```text
hidden_size × activation_bytes
```

Prefill transfer across boundaries:

```text
prompt_tokens × hidden_size × activation_bytes × boundaries
```

The bottleneck is usually RTT, queue and the slowest stage rather than steady-state bandwidth.

### 12.2 Tensor groups

- same host GPU group;
- trusted LAN/RDMA rack;
- no unrestricted WAN all-reduce;
- topology changes require re-benchmark.

### 12.3 CPU contribution

CPU can provide ingress, policy, local small models, perception, cache, verification, auditing and quantized small stages. It is not equivalent GPU capacity and must not become the slow stage merely to maximize participation.

### 12.4 Cross-device support

Use a cross-platform protocol and node agent, but validate runtime backends per device. Mobile and constrained devices default to ingress, perception and local models.

## 13. Multi-modal privacy

| Mode | Data path | Use |
| --- | --- | --- |
| `local_only` | Sensor and model stay local | Private/high-risk tasks |
| `redacted_features` | Text, transcript, boxes or embeddings with declared leakage | General multi-modal tasks |
| `encrypted_full_media` | Explicitly authorized encrypted media to allowed nodes | Detailed visual/audio understanding |

Task encryption covers the path from source features/media to the final consumer. Ingress confidentiality is a separate trust assumption.

## 14. Security

- membership certificates and revocation;
- tenant/user grants separate from node identity;
- short capacity leases and policy epochs;
- signed model/runtime manifests;
- worker sandbox and least privilege;
- request/idempotency deadlines and rate limits;
- bounded peer URLs and outbound destinations;
- signed receipts for accounting and audit;
- no custom unsigned code on arbitrary workers.

Random duplicate execution is a risk-control mechanism, not a proof of correctness against colluding nodes.

## 15. Failure semantics

| Failure | Response |
| --- | --- |
| Stale discovery record | TTL expiry and fresh probe |
| Stage unavailable before output | Replan within deadline/budget |
| Failure after first token | Stop; no transparent replay |
| Ingress failure | Client reconnects; no seamless guarantee without migration design |
| Cold model stage | Reserve hot replica or accept stated start-up latency |
| Planned shutdown | Freeze admission, drain, checkpoint, replicate and sign receipt |
| Unexpected power loss | Recover committed/WAL state; unconfirmed writes may be lost |

Request states:

- `pre_admission`;
- `admitted`;
- `prefill`;
- `streaming`;
- `committed`;
- `failed_recoverable`;
- `failed_terminal`.

## 16. Research hypotheses

| ID | Hypothesis | Baseline | Primary metrics |
| --- | --- | --- | --- |
| H1 | A 2–3-stage WAN pipeline can serve a model that a single participant cannot hold | Single-node quantization/offload, LAN pipeline | TTFT, ITL, throughput, memory |
| H2 | Capability-aware placement beats random and RTT-only routing | Random/RTT/static | P95 latency, failures, WAN bytes |
| H3 | Local perception compression reduces traffic without unacceptable quality loss | Raw media | Bytes, CER, WER, task accuracy |
| H4 | Signed leases reduce false routing and retry storms | No lease | Timeouts, invalid retries, duplicate work |
| H5 | Pre-output failover improves completion rate | Retry only | Completion, P95 recovery |
| H6 | Local small-model routing improves effective system throughput | Always remote large model | Completed work, GPU queue, cost |
| H7 | Multi-dimensional capacity profiles beat device/peak labels | Device only/RTT only | Misplacement, OOM, thermal aborts |
| H8 | Dynamic whole-model vs pipeline selection beats fixed execution mode | Fixed mode | TTFT, completion, WAN bytes, energy |
| H9 | Model/task/SLA-specific strong/weak labels reduce role oscillation | Permanent label | Misclassification, OOM, role changes |
| H10 | Group/domain views reduce discovery cost without creating global dependency | Full DHT | Query count, planning latency, failover |
| H11 | Drain and replica receipts bound shutdown data loss | Immediate exit | Lost confirmed writes, RTO, duplicates |
| H12 | Resource pledges and failure-domain repair improve role durability | Ad hoc backup | Backup SLO, recovery point, impact |
| H13 | Online pooled capacity exceeds local-only capability under policy | Local only | Model size, TTFT, completion, fairness |
| H14 | Tiered encrypted memory reduces local storage while preserving recall | All local hot | Storage, Recall@K, cold recall, unrecoverable objects |

## 17. Fixed benchmark scenarios

- one allowed open model family;
- one local 1B–3B fallback;
- one model requiring at least two execution nodes;
- text, OCR, ASR and image-text tasks;
- fixed seeds and sampling parameters;
- short/medium/long context classes;
- identical model/artifact versions across hardware experiments;
- single-node reference baseline;
- recorded hardware, runtime, quantization and license.

## 18. Metrics

- TTFT, ITL, tokens/s and completion rate;
- P50/P95/P99 latency;
- WAN upload/download per request;
- queue, utilization and per-stage time;
- sustained 15–30-minute throughput and thermal throttling;
- energy per token;
- role misclassification and oscillation;
- group capacity error and failover;
- drain receipt completion and power-loss recovery;
- backup SLO and replica-domain coverage;
- online/offline transition and duplicate writes;
- memory Recall@K, token cost and cold restore;
- OCR CER, ASR WER and multi-modal accuracy;
- unauthorized routing, duplicate receipts and license violations.

## 19. Network and fault matrix

- process-local;
- LAN;
- metro;
- cross-carrier;
- cross-region;
- server/desktop/laptop/phone/ARM mixes;
- Ethernet/Wi-Fi/cellular;
- home NAT;
- symmetric NAT/CGNAT;
- relay fallback;
- random 1–10% node loss;
- stage OOM/process crash;
- bootstrap outage.

## 20. Roadmap

### Phase 0: freeze research boundary

- ADRs and core schemas;
- request/stage/role state machines;
- select local and pipeline models;
- benchmark request set;
- license and data map.

### Phase 1: trusted LAN

- 4–6 nodes including phone ingress and ARM cache;
- two GPU stages;
- text and compressed multi-modal request;
- whole-model vs pipeline comparison;
- role migration and backup;
- desktop spatial mock.

Exit:

- 1,000 fixed requests without undetected stage mismatch;
- quality within two points of reference;
- P95 TTFT at most 2× single-node reference;
- pipeline throughput at least 60% of reference;
- crash detected and explicit;
- no unconfirmed durability marked D2/D3.

### Phase 2: cross-region invitation network

- 6–12 nodes across 2–3 network locations;
- 2–3 stage replicas;
- QUIC/AutoNAT/DCUtR/relay;
- capacity leases and domain catalogs;
- online/offline transition;
- thermal, battery and NAT experiments.

Exit:

- ≥95% invited-node join success;
- ≥70% direct-hole-punch success where expected;
- relay fallback does not loop;
- ≥95% pre-output fault failover;
- <1% OOM/thermal abort from misclassification;
- 99% backup policy satisfaction for high-value roles;
- no quota or duplicate-accounting violation in 100 disconnect tests.

### Phase 3: multi-modal research

- 20–30 invited nodes;
- three privacy modes;
- local/remote model collaboration;
- memory cold recall;
- duplicate-execution sampling;
- 24-hour stability.

### Phase 4: before public participation

- independent threat review;
- abuse process;
- model/data license review;
- identity/revocation/accounting mechanisms;
- evidence that WAN distribution provides real benefit.

## 21. Stop and pivot conditions

1. If P95 WAN pipeline TTFT exceeds 3× local reference and capacity gain is under 30%, pause WAN pipeline work.
2. If failures after first token cannot be recovered, do not claim self-healing.
3. If perception compression exceeds accuracy thresholds, keep selective raw-media mode.
4. If identity/abuse/settlement cannot be bounded, do not open anonymous nodes.
5. If duplicate execution cost exceeds its risk-control benefit, switch to invited audit and anomaly-triggered recomputation.
6. If a backend cannot pass manifest compatibility, exclude it from the default pool.
7. If mobile devices cannot meet background/energy rules, keep them as ingress/perception only.
8. If group neurons do not materially improve target workloads, treat them as cache/management groups.
9. If strong/weak labels remain unstable with hysteresis, use per-request leases only.

## 22. Prior-art perspective

Petals demonstrates internet-distributed pipeline inference and fine-tuning. Existing work therefore makes generic “P2P model sharding” insufficient as a novelty claim. NeuronMesh must validate the combination of:

- model/task/SLA-specific capacity derivation;
- short leases and ingress-local planning;
- whole-model vs pipeline dynamic selection;
- host-independent role memory with failure-domain durability;
- evidence-gated local adapter learning.

## 23. Final recommendation

Proceed only as an incremental, evidence-driven research programme. First establish a reproducible trusted cell and failure semantics. Add WAN transport and pipeline execution only after single-node baselines show meaningful capacity or quality benefit.
