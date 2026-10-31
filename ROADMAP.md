# NeuronMesh Roadmap

[English](ROADMAP.md) | [简体中文](ROADMAP.zh-CN.md)

The roadmap is organized by architecture gates, not feature count. A gate is complete only when its contracts, automated tests and failure tests exist. Gate definitions are normative in [ARCHITECTURE.md](ARCHITECTURE.md#19-implementation-gates).

## v0.2.0 — Runnable reference slice

- [x] Ed25519 node identity and signed capability records;
- [x] device, sustained-performance and resource-pledge profiles;
- [x] invite-only HTTP peer mesh and entry-side remote selection;
- [x] online and offline-autonomous modes;
- [x] AES-GCM memory, HMAC blind index and hot/warm/cold tiers;
- [x] remote encrypted replicas, cold recall and best-effort deletion propagation;
- [x] storage admission and quota enforcement;
- [x] virtual-role export/import with transfer-key re-encryption;
- [x] safe drain, WAL checkpoint and signed shutdown receipt;
- [x] OpenAI-compatible API, readiness and operations CLI;
- [x] spatial-session mock interface and action permission broker;
- [x] live host/role graph with activity-driven relation pulses.

This release is not a complete implementation of the architecture baseline.

## Unreleased — Architecture baseline

- [x] target system architecture and implementation-gap matrix;
- [x] state ownership, request/lease/memory/role failure contracts;
- [x] versioned interface inventory;
- [x] architecture threat model and residual-risk register;
- [x] observable quality scenarios and architecture-gated roadmap.

## v0.3.0 — Architecture and trust baseline

- [ ] Convert core architecture objects to versioned JSON Schemas with conformance fixtures;
- [ ] Implement critical-field compatibility and migration rules;
- [ ] Replace invitation-wide bearer credentials for external pilots with node mTLS and namespace-scoped tenant grants;
- [ ] Add request size, rate, concurrency, egress and context budgets;
- [ ] Validate peer URLs and prevent credential-forwarding redirects/SSRF;
- [ ] Define signed execution, storage, deletion and capacity receipts;
- [ ] Add policy epochs, idempotency keys and fencing tokens;
- [ ] Add a state-machine test harness for expiry, replay, revocation and partition.

**Gate:** incompatible manifests and unauthorized requests fail before a worker starts.

## v0.4.0 — Trusted-cell execution

- [ ] Run 3–6 heterogeneous nodes in one invitation domain;
- [ ] Implement local-small and remote-whole-model routing with capacity leases;
- [ ] Add llama.cpp/vLLM adapter conformance fixtures;
- [ ] Add real native streaming, cancellation and deadline propagation;
- [ ] Implement signed step receipts and quota accounting;
- [ ] Test worker crash before and after first output.

**Gate:** no duplicate settlement; safe retry boundaries are explicit.

## v0.5.0 — Real distributed inference

- [ ] Freeze model, tokenizer, template, runtime and stage manifests;
- [ ] Implement contiguous 2–3 stage activation transport;
- [ ] Add activation-shape/dtype validation and backpressure;
- [ ] Compare remote whole-model, local offload and pipeline baselines;
- [ ] Add trusted LAN tensor-group experiment only if pipeline evidence justifies it;
- [ ] Complete NAT and network-matrix tests for the chosen transport.

**Gate:** quality, TTFT, ITL, throughput and resource use are reproducible against fixed baselines.

## v0.6.0 — Durable memory and portable roles

- [ ] Namespace key hierarchy, owner recovery and rotation drills;
- [ ] Immutable memory versions, replica manifests and conflict semantics;
- [ ] Anti-entropy, scrub, delete debt and tombstone expiration;
- [ ] Repair-before-eviction and capacity-pressure migration;
- [ ] Fenced virtual-role primary epochs;
- [ ] Automatic migration preparation, target verification and rollback;
- [ ] Offline recovery and key-loss exercises.

**Gate:** every durability level has measured RPO/RTO and a stated failure boundary.

## v0.7.0 — Trusted wide-area federation

- [ ] Authenticated QUIC/libp2p transport;
- [ ] Multi-bootstrap discovery and bounded domain catalogs;
- [ ] AutoNAT, DCUtR and Circuit Relay v2 fallback;
- [ ] Revocation propagation and partition recovery;
- [ ] Cross-domain policy composition and abuse limits;
- [ ] Catalog failure and relay saturation tests.

**Gate:** cross-domain operation without anonymous exposure or a global scheduler.

## v0.8.0 — Persistent learning

- [ ] Consent and evidence-gated candidate data pipeline;
- [ ] Signed local Adapter training manifests;
- [ ] Replaceable aggregation experiment;
- [ ] Compatibility, regression, poisoning and privacy gates;
- [ ] Canary rollout, monitoring and rollback;
- [ ] Machine-unlearning and contribution-impact audits.

**Gate:** no model update enters rollout without traceable data/update lineage and evaluation evidence.

## v0.9.0 — Spatial ecosystem

- [ ] Desktop spatial simulator and WebXR conformance fixture;
- [ ] Versioned event ordering, expiry and action grants;
- [ ] OpenXR/Unity/Unreal adapter boundary;
- [ ] Bystander privacy and sensor-retention tests;
- [ ] Role-to-avatar binding with fenced epochs.

## Explicit non-goals for the current release

- anonymous public-node participation;
- one global scheduler or global mutable model owned by every node;
- public-internet all-reduce or unrestricted tensor parallelism;
- claims of permanent, physically indestructible memory;
- automatic global training from conversations;
- a token economy before identity, abuse and accounting controls;
- production SLA, regulated-data handling or security certification.

