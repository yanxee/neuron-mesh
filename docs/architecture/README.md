# Architecture Reading Room

NeuronMesh is a long-running systems research programme. This directory holds the contracts that a feature must satisfy before it is treated as part of the platform.

## Current baseline

- [System architecture](../../ARCHITECTURE.md): target planes, components, state ownership, gates and implementation gap.
- [State and failure model](STATE_AND_FAILURE.md): request, lease, memory and role state machines plus failure tests.
- [Interface contracts](INTERFACE_CONTRACTS.md): versioned objects shared between nodes and services.
- [Threat model](THREAT_MODEL.md): trust boundaries, threat register, controls and residual risk.
- [Decision log](DECISIONS.md): architecture decisions already taken and their reversal cost.
- [Quality scenarios](QUALITY_SCENARIOS.md): observable acceptance outcomes for scheduling, failure, memory, roles, security and learning.

## Status language

| Status | Meaning |
| --- | --- |
| `Proposed` | Under discussion; no implementation commitment |
| `Accepted` | Required direction for new work; implementation may be partial |
| `Implemented` | Contract, conformance tests and failure tests exist |
| `Superseded` | Replaced by a linked decision |

The current repository must be described as a reference slice unless the `Implemented` condition is met.

## Change checklist

Any architecture-impacting change must describe:

1. authoritative state owner;
2. lifecycle and idempotency;
3. compatibility and migration;
4. failure, partition and retry behavior;
5. security and privacy boundary;
6. receipts and telemetry;
7. conformance evidence;
8. rollback/degradation path;
9. unsupported cases.

The architecture is expected to remain incomplete for multiple releases. A smaller verified subsystem is preferable to a broad unverified claim.
