# Join NeuronMesh

NeuronMesh is a runnable research prototype for capability-aware decentralized LLM inference, encrypted persistent memory and continual learning across heterogeneous hosts.

It is early enough that a small, well-tested contribution can shape the architecture. It is also deliberately honest: public-internet P2P transport, real cross-node Transformer execution, federated training and production security are roadmap items, not current claims.

**Project:** <https://github.com/yanxee/neuron-mesh>

**Website:** <https://yanxee.github.io/neuron-mesh/>

**Architecture:** <https://github.com/yanxee/neuron-mesh/blob/main/ARCHITECTURE.md>

**Tasks:** <https://github.com/yanxee/neuron-mesh/blob/main/docs/CONTRIBUTOR_TASKS.md>

## Pick a route

### 1. Verify the prototype — about 10 minutes

Best for first-time visitors, node operators and compatibility testers.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

On Linux/macOS, see [DEMO.md](DEMO.md). No model download or GPU is required because the test uses a deterministic Echo backend.

Useful result: a [compatibility report](https://github.com/yanxee/neuron-mesh/issues/new?template=deployment_report.yml) containing the operating system, CPU architecture, Python version, exact command and non-secret output.

### 2. Ship one scoped fix — 30 to 90 minutes

Browse [good first issues](https://github.com/yanxee/neuron-mesh/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22). Comment on the issue before starting. Small changes are welcome when they include a test or reproducible evidence.

Good starting areas:

- streamed remote-inference tests;
- storage-quota boundary behavior;
- Docker Compose smoke testing;
- backend adapter conformance;
- role-migration failure recovery;
- documentation, diagrams and translations.

### 3. Bring a research question — one afternoon or longer

Choose one measurable question rather than debating the whole vision:

- Does capability-aware placement beat round-robin and RTT-only routing under the same workloads?
- Does hot/warm/cold encrypted recall reduce prompt-token cost without unacceptable latency?
- How do memory consolidation and replay affect factual accuracy, staleness and forgetting?
- When does LAN pipeline parallelism outperform whole-model provider routing on a WAN?
- Which failures produce false durability, stale replicas or unrecoverable role state?
- How should malicious memory, model updates and node telemetry be quarantined?

Publish a baseline, hardware, workload, metric, acceptance threshold and failure modes. A negative but reproducible result is a valid contribution.

### 4. Review a protocol boundary

Start with the [architecture baseline](../ARCHITECTURE.md), [state and failure model](architecture/STATE_AND_FAILURE.md) and [interface contracts](architecture/INTERFACE_CONTRACTS.md). The project intentionally distinguishes accepted target architecture from implemented behavior.

We especially need adversarial review in:

- distributed systems and NAT traversal;
- namespace authorization, key wrapping and recovery;
- encrypted replica deletion and rollback semantics;
- model and worker supply-chain trust;
- inference scheduling under thermal, battery and network changes;
- WebXR/OpenXR privacy and permission boundaries.

Open a Discussion with the threat model or a design issue with concrete alternatives. Do not expect the core team to have solved these problems already.

### 5. Contribute context instead of code

You can help by sharing real hardware measurements, a failed deployment, a university course exercise, an accessibility review, an operator checklist or a translation. These are research inputs when they include enough evidence for another person to reproduce the observation.

## Help wanted now

| Area | Current priority |
| --- | --- |
| Architecture | Convert core contracts into versioned schemas and state-machine tests |
| Transport | Evaluate libp2p QUIC, AutoNAT/DCUtR and relay failure modes |
| Inference | Define worker and stage-manifest contracts for llama.cpp/vLLM |
| Memory | Measure context cost, recall quality and encrypted restore latency |
| Learning | Design an isolation-safe federated adapter experiment |
| Trust | Replace the invitation-wide token with namespace authorization |
| Reliability | Add chaos, Docker and NAT-matrix tests |
| Interfaces | Define a platform-neutral WebXR/OpenXR adapter boundary |

## What “done” means

A contribution is ready when another person can:

1. understand the intended behavior;
2. reproduce the result with the documented command or workload;
3. identify the failure boundary and security assumptions;
4. run automated checks without hidden credentials or proprietary data;
5. maintain the change without relying on undocumented local state.

## Contributor agreement

- Be specific and kind; critique the evidence and design, not the person.
- Do not present a roadmap item as an implemented capability.
- Do not upload private memory, credentials or unlicensed model artifacts.
- Report exploitable security issues privately as described in [SECURITY.md](../SECURITY.md).
- Disclose substantial AI assistance and remain accountable for the contribution.
- Ask for help early. A well-scoped partial result is more useful than a silent rewrite.

All contribution types are eligible for release-note credit and progression toward reviewer or maintainer responsibilities as described in [GOVERNANCE.md](../GOVERNANCE.md).

## Start a conversation

- [GitHub Discussions](https://github.com/yanxee/neuron-mesh/discussions): open questions and design exploration
- [Issues](https://github.com/yanxee/neuron-mesh/issues): actionable defects, tasks and benchmarks
- [Architecture proof questions](architecture/QUALITY_SCENARIOS.md): observable scenarios an implementation must satisfy
- [Research proposal](https://github.com/yanxee/neuron-mesh/issues/new?template=research_proposal.yml): a hypothesis with a reproduction plan
- [Compatibility report](https://github.com/yanxee/neuron-mesh/issues/new?template=deployment_report.yml): demo and deployment results
