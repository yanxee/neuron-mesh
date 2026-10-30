# Architecture Decision Log

This is a lightweight ADR index for the initial architecture baseline. A future change should add a dedicated record that describes alternatives, evidence, consequences and reversal cost.

| ID | Decision | Status | Consequence |
| --- | --- | --- | --- |
| AD-001 | Model the network as federated invitation domains | Accepted | No implicit global administrator or global scheduler |
| AD-002 | Separate membership, discovery/planning, execution, durable state, learning and observability planes | Accepted | Independent failure behavior and clearer state ownership |
| AD-003 | Use node identity plus short-lived capacity leases | Accepted | Invitation and hardware claims cannot directly schedule work |
| AD-004 | Prefer local small models or remote whole-model execution before public-WAN pipelines | Accepted | Pipeline complexity must prove measurable benefit |
| AD-005 | Treat streaming output as irreversible after first token | Accepted | Transparent retry is forbidden after output begins |
| AD-006 | Define durability as D0-D3 contracts with measured RPO/RTO | Accepted | “Permanent memory” is removed from technical claims |
| AD-007 | Keep non-parametric memory separate from parameter training | Accepted | Conversation data cannot directly trigger global weight changes |
| AD-008 | Require fenced primary epochs for virtual roles | Accepted | Manual export/import remains a migration prototype |
| AD-009 | Content-address models, tokenizers, templates, runtimes and training updates | Accepted | Unknown or mismatched artifacts fail closed |
| AD-010 | Treat spatial interfaces as optional versioned adapters | Accepted | WebXR/OpenXR cannot become a core dependency |
| AD-011 | Bind accounting to idempotent signed receipts | Accepted | Retries cannot silently produce duplicate settlement |
| AD-012 | Require single-node baseline and partition/failure test for distributed features | Accepted | A distributed feature cannot be accepted only by a happy-path demo |

## Required record template

```text
ADR number and title
Status
Context and affected users
Decision
Alternatives considered
Evidence and experiments
State owner and lifecycle impact
Security/privacy impact
Compatibility and migration
Rollback and degraded behavior
Unsupported cases
Reviewers and date
```

Protocol, storage, identity, durable-memory, scheduling and training changes require an accepted decision record before implementation.
