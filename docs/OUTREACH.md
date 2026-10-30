# Outreach Kit

Use these materials to invite collaborators without overstating the current implementation.

## One-sentence pitch

NeuronMesh is an open-source research network exploring capability-aware distributed LLM inference, encrypted persistent memory and continual learning across heterogeneous nodes.

## Short announcement

NeuronMesh v0.2.0 is a runnable research MVP for decentralized LLM infrastructure. It includes signed node capabilities, entry-side routing, an OpenAI-compatible API, AES-GCM memory, cross-failure-domain encrypted replicas, role migration, safe drain receipts and a two-node integration test. We are looking for contributors in distributed systems, LLM serving, memory consolidation, federated learning, security and WebXR.

## Call for contributors

We need help turning the research skeleton into a reproducible platform:

- libp2p QUIC, DHT and NAT traversal
- real llama.cpp and vLLM stage workers
- memory consolidation and retrieval benchmarks
- federated LoRA and unlearning research
- namespace authorization and encrypted key recovery
- Docker, observability and chaos testing
- WebXR/OpenXR adapters

Start here: [Contributor task board](CONTRIBUTOR_TASKS.md).

## Suitable channels

- GitHub Discussions and issues
- University distributed-systems and AI systems groups
- Local open-source meetups
- LLM serving and inference engineering communities
- Edge computing and WebXR research communities

## Honest framing

Always state:

- This is `v0.2.0` research software.
- Online discovery currently uses an invite-only HTTP mesh.
- Public-internet P2P transport is planned, not implemented.
- The default backend is deterministic Echo; real inference uses a configured OpenAI-compatible worker.
- “Persistent memory” means encrypted replication and recovery, not physically permanent storage.

## Canonical links

- Repository: <https://github.com/yanxee/neuron-mesh>
- Website: <https://yanxee.github.io/neuron-mesh/>
- Roadmap: <https://github.com/yanxee/neuron-mesh/blob/main/ROADMAP.md>
- Contributor tasks: <https://github.com/yanxee/neuron-mesh/blob/main/docs/CONTRIBUTOR_TASKS.md>

