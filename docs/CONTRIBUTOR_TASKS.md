# Contributor Task Board

These are scoped starting points for new contributors. Read [Join NeuronMesh](JOIN.md) first, then comment on or open the corresponding issue before starting a task that changes an API, benchmark claim or storage format.

## How to claim work

1. Choose a result you can finish and verify, not an entire subsystem.
2. Comment with the artifact you plan to produce and the command or metric that will prove it.
3. Keep the first pull request focused. Documentation, a failing test or a reproducible benchmark is a valid result.
4. If the task is already larger than one reviewable change, propose a smaller first slice.

Tasks are not reserved until a maintainer or current claimant confirms the overlap. If an issue is quiet for 14 days and no draft exists, another contributor may ask to continue it.

## Good first contributions

### 1. Add streamed remote inference proxy tests — [issue #1](https://github.com/yanxee/neuron-mesh/issues/1)

- Add tests for gateway-to-gateway SSE forwarding.
- Verify disconnect propagation, timeout and `X-Neuron-Forwarded` loop prevention.
- Expected files: `neuron_mesh/peers.py`, `tests/test_api.py`.

### 2. Add storage-quota boundary tests — [issue #2](https://github.com/yanxee/neuron-mesh/issues/2)

- Test replacing an existing backup with a larger or smaller payload.
- Test HTTP 507 when the pledge would be exceeded.
- Verify no partial replica acknowledgement is reported.

### 3. Add a network capability probe

- Measure bidirectional latency, jitter and approximate throughput between two nodes.
- Persist an EWMA result without overwriting a peer's signed static capability.
- Provide configurable timeouts and a deterministic test double.

### 4. Add role migration failure recovery

- Add an endpoint or command to return a source role from `migrating` to `active`.
- Test wrong target IDs, wrong transfer secrets and expired transfer policies.

### 5. Add namespace authorization

- Introduce owner-scoped tokens instead of one invitation-wide bearer token.
- Add tests proving one namespace cannot read another.
- Document migration from the development token.

### 6. Add Docker smoke tests — [issue #3](https://github.com/yanxee/neuron-mesh/issues/3)

- Add a CI job that validates Compose configuration and starts two containers.
- Verify readiness, peer discovery, memory replication and cold recall.

### 7. Add a terminal demo recording script

- Make a deterministic demo using the Echo backend.
- Show status, remote route, encrypted backup and cold recall.
- Publish a transcript under `docs/`.

### 8. Add model backend adapter contract

- Define a stable interface for llama.cpp, vLLM and test backends.
- Include model listing, health, chat and cancellation.
- Add a mock adapter and conformance tests.

## Research contributions

### 9. Benchmark resource-aware placement

Compare random, RTT-only and full capability-aware routing with fixed hardware and workloads.

### 10. Benchmark hot/warm/cold memory policies

Compare local-only, hot tier plus remote backups, and adaptive eviction. Report Recall@K, token cost, storage and restore latency.

### 11. Evaluate memory poisoning defenses

Build a canary set for cross-session injection and measure quarantine, false positives and usability cost.

### 12. Measure host-type behavior

Test at least a server, desktop, laptop and ARM small host under heat, battery and network changes. Publish sustained throughput rather than peak benchmark numbers.

### 13. Run the compatibility lab

- Run the deterministic two-node demo on Windows, Linux, macOS or a small ARM device.
- Report OS, architecture, Python version, Docker availability, exact commands and non-secret output.
- Open a compatibility/deployment report even when it fails.
- Turn repeated failures into a focused bug with a reduced reproduction.

### 14. Write the public-internet transport decision record

- Compare libp2p QUIC with a minimal authenticated HTTPS/WebTransport design.
- Cover NAT traversal, relay fallback, identity binding, replay, discovery and partition recovery.
- Include a test matrix for home NAT, CGNAT, mobile links and blocked UDP.
- This is an architecture proposal, not a requirement to implement the entire transport in the first PR.

### 15. Specify the spatial adapter conformance suite

- Define version negotiation, permission checks, disconnect behavior and bounded event ordering.
- Provide a browser mock and one engine-neutral fixture.
- Include bystander privacy and untrusted model-output cases.
- Keep WebXR/OpenXR optional dependencies behind the adapter.

## Task quality bar

A task is ready for a new contributor when it states:

- the current behavior and why it is insufficient;
- the smallest acceptable result;
- a reproducible verification command or metric;
- relevant files or documents;
- explicit non-goals and failure boundaries.

## How to propose work

Use the feature request issue template and include:

1. The problem and affected users.
2. A minimal testable change.
3. A benchmark or correctness criterion.
4. Failure modes and non-goals.
5. Whether the work changes protocol, memory or trust semantics.

