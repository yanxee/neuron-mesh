# Contributing to NeuronMesh

NeuronMesh is an early research project. Small, testable and clearly documented contributions are welcome. You do not need to implement the whole vision or run a large model to help.

New here? Use the [contributor entry guide](https://yanxee.github.io/neuron-mesh/join.html) to choose a path based on the time and expertise you want to offer.

## Choose a contribution

| You can offer | A useful first contribution |
| --- | --- |
| A computer or browser | Run the [10-minute demo](docs/DEMO.md) and publish a compatibility report |
| Python and testing | Claim a `good first issue` with clear acceptance criteria |
| Distributed systems | Review the transport design, NAT matrix or failure-recovery semantics |
| LLM serving | Add a llama.cpp/vLLM adapter or stage-execution conformance test |
| Research | Propose a reproducible hypothesis with a baseline, metric and failure boundary |
| Security/privacy | Review namespace authorization, key lifecycle, poisoning or abuse controls |
| Documentation/design | Improve onboarding, diagrams, translations or experiment reports |
| WebXR/OpenXR | Define an adapter contract without coupling the core to one engine |

Open-ended questions belong in [GitHub Discussions](https://github.com/yanxee/neuron-mesh/discussions). Use an issue when there is a concrete change, test or experiment that another person can verify.

## First contribution workflow

1. Pick an open issue, or open a short design issue before changing an API, storage format or trust boundary.
2. Comment with the result you plan to produce and the boundary you will test. A maintainer will confirm scope if needed.
3. Fork the repository and make a focused change on a topic branch.
4. Run the verification command below and include the output or a link to CI in the pull request.
5. Explain user-visible behavior, failure modes and any unresolved limitation in the pull request.

Maintainer response is best effort. New issues and pull requests are normally triaged within three business days; a polite ping after that is welcome.

## Development setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
ruff check .
pytest
python scripts/e2e_check.py
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

All of the following must pass before a pull request is ready for review:

```powershell
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\e2e_check.py
```

## Pull requests

- Keep the OpenAI-compatible and internal APIs backward compatible unless the change is explicitly versioned.
- Add tests for routing, memory durability, permissions and failure recovery.
- Keep changes reviewable. Split unrelated refactors, protocol changes and formatting churn.
- Do not put raw credentials, user memory or model weights in the repository.
- Preserve the distinction between implemented capabilities and roadmap items.
- Include performance numbers with hardware, model, prompt/output lengths and network conditions.
- Include a short migration note for configuration, storage-format or API changes.
- Disclose substantial AI assistance and remain accountable for every submitted line.

## Research claims

Claims about memory persistence, fault recovery, decentralization or model quality must include a reproducible test and a clearly stated failure boundary.

Architecture-impacting changes must also identify the authoritative state owner, lifecycle/idempotency behavior, compatibility and migration path, partition/failure behavior, security boundary and rollback path. Start with [ARCHITECTURE.md](ARCHITECTURE.md) and the [architecture change checklist](docs/architecture/README.md#change-checklist).

Use this evidence template for experiments and benchmarks:

```text
Question:
Current behavior and baseline:
Hypothesis:
Hardware / OS / software versions:
Workload and random seeds:
Metrics and acceptance threshold:
Observed result:
Failure modes and threats to validity:
Artifact or reproduction command:
```

Negative results are useful when the test is reproducible. Do not tune a headline number without publishing the workload that produced it.

## Documentation, translations and compatibility reports

Small non-code contributions count. A compatibility report should include the operating system, CPU architecture, Python version, whether Docker was used, the exact commands, expected output and the complete non-secret error message. A translation should keep research claims, limitations and security warnings equivalent to the source document.

## Review and recognition

Review focuses on correctness, reproducibility, security boundaries and maintainability. A contributor may be invited to review a subsystem after demonstrating sound judgment in that area. Code, tests, benchmarks, protocol analysis, documentation, translations and reproduced deployment reports are credited in release notes; contributors may opt out of public attribution.

See [GOVERNANCE.md](GOVERNANCE.md) for decision-making and the contributor ladder.

