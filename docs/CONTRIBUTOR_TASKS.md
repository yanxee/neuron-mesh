# Contributor Task Board

These are scoped starting points for new contributors. Open an issue before starting a task that changes an API or storage format.

## Good first contributions

### 1. Add streamed remote inference proxy tests

- Add tests for gateway-to-gateway SSE forwarding.
- Verify disconnect propagation, timeout and `X-Neuron-Forwarded` loop prevention.
- Expected files: `neuron_mesh/peers.py`, `tests/test_api.py`.

### 2. Add storage-quota boundary tests

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

### 6. Add Docker smoke tests

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

## How to propose work

Use the feature request issue template and include:

1. The problem and affected users.
2. A minimal testable change.
3. A benchmark or correctness criterion.
4. Failure modes and non-goals.
5. Whether the work changes protocol, memory or trust semantics.

