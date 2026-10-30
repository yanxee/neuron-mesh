# Provisional Governance

[English](GOVERNANCE.md) | [简体中文](GOVERNANCE.zh-CN.md)

NeuronMesh is currently a research prototype. Governance is intentionally lightweight and will evolve as the contributor base grows.

## Current roles

| Role | Responsibilities |
| --- | --- |
| Maintainer | Roadmap, releases, security response, final merge decisions |
| Research contributor | Reproducible experiments, design analysis, benchmark reports |
| Code contributor | Code, tests, documentation and deployment integration |
| Reviewer | Technical review in an area of demonstrated familiarity |
| Community participant | Bug reports, use cases, questions and protocol feedback |

## Decisions

- Small fixes can be merged after tests and one maintainer review.
- API, storage-format or trust-model changes require a short design issue before implementation.
- Claims about decentralization, memory persistence or model performance require a reproducible benchmark or clearly labeled hypothesis.
- The maintainer makes provisional final decisions while the project has fewer than three regular maintainers.
- When three or more regular maintainers exist, protocol changes will use a documented lazy-consensus process with a public decision record.

## Promotion

NeuronMesh uses a contribution ladder rather than a fixed waiting period. Promotion requires demonstrated judgment, constructive review and reliable follow-through; contribution volume alone is not sufficient.

| Stage | Evidence | Responsibility |
| --- | --- | --- |
| Participant | Question, compatibility report, issue or reproduced result | Share context and evidence |
| Contributor | One accepted code, test, research, documentation or deployment artifact | Own scoped results and respond to review |
| Returning contributor | Multiple accepted contributions across at least two tasks | Help refine scope and reproduce others' results |
| Reviewer | Repeated sound reviews or a validated subsystem contribution | Request changes within an explicit area |
| Maintainer | Sustained stewardship, sound protocol judgment and reliable releases | Roadmap, releases, security response and final merge decisions |

Any person may propose a contributor for a new stage in a public issue. The affected person must accept the responsibility before it is recorded. Reviews and benchmarks are credited in the same way as code. Contributors may remain anonymous in public recognition.

## Community commitments

- New issues and pull requests are triaged on a best-effort basis, normally within three business days.
- Actionable work has a reproduction path, acceptance criterion and explicit non-goals.
- The project distinguishes tested behavior from hypotheses and roadmap items.
- Maintainers document material design decisions and acknowledge mistakes when evidence changes.
- Participation is judged by conduct and contribution quality, not affiliation or model choice.

## Security

Security reports follow [SECURITY.md](SECURITY.md). Security-sensitive decisions may be handled privately until a coordinated disclosure is ready.

