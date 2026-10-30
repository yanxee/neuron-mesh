# NeuronMesh Roadmap

## v0.2.0 — Current research MVP

- [x] Ed25519 node identity and signed capability records
- [x] Device, sustained-performance and resource-pledge profiles
- [x] Invite-only HTTP peer mesh and entry-side remote selection
- [x] Online resource-pool and offline-autonomous modes
- [x] AES-GCM memory, HMAC blind index and hot/warm/cold tiers
- [x] Remote encrypted replicas, cold recall and deletion propagation
- [x] Storage admission and quota enforcement
- [x] Virtual-role export/import with transfer-key re-encryption
- [x] Safe drain, WAL checkpoint and signed shutdown receipt
- [x] OpenAI-compatible API, readiness and operations CLI
- [x] Spatial-session mock interface and action permission broker

## v0.3.0 — Network transport

- [ ] Replace the HTTP discovery MVP with libp2p QUIC and authenticated streams
- [ ] Add AutoNAT, DCUtR and Circuit Relay v2 fallback
- [ ] Implement signed Kademlia capability records with TTL
- [ ] Add multi-bootstrap and domain capability replication
- [ ] Build NAT matrix tests and network-partition recovery tests

## v0.4.0 — Real distributed inference

- [ ] Integrate llama.cpp, vLLM and OpenAI-compatible worker adapters
- [ ] Implement contiguous Transformer stage manifests
- [ ] Add pipeline-stage activation transport and deadline admission
- [ ] Add local tensor groups for LAN/RDMA workers
- [ ] Benchmark public-WAN pipeline versus whole-model provider routing

## v0.5.0 — Persistent learning

- [ ] Namespace key wrapping and owner-controlled key recovery
- [ ] Scheduled local memory consolidation and evidence gating
- [ ] Federated LoRA adapter training with replaceable aggregators
- [ ] Compatibility-aware replay, regression gates and rollback
- [ ] Machine-unlearning and contribution-impact audits

## v0.6.0 — Spatial and ecosystem interfaces

- [ ] WebXR adapter and desktop spatial simulator
- [ ] OpenXR/Unity/Unreal adapter boundary
- [ ] Role-to-avatar binding and bystander privacy controls
- [ ] Agent framework compatibility conformance suite

## Explicit non-goals for the current release

- Anonymous public-node participation
- Public-Internet all-reduce or unrestricted tensor parallelism
- Claims of permanent, physically indestructible memory
- Real-money incentives or an unaudited global ledger
- Production SLA, regulated-data handling or security certification

