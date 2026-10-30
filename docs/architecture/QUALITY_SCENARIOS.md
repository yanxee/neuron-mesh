# Architecture Quality Scenarios

**Status:** Acceptance scenario baseline `v0.1`

These scenarios define observable outcomes for the architecture. A scenario marked **target** is not implemented yet.

## 1. Capacity selection

### QS-01: A high-spec node is under thermal pressure

**Given** a GPU node advertises a completed benchmark for a model stage  
**and** its current temperature or power policy no longer permits the promised sustained rate  
**When** an ingress requests capacity  
**Then** the node offers reduced capacity or rejects the stage  
**and** the planner does not select it for a latency-critical lease  
**and** the previous strong classification is not used as proof of current availability.

Evidence: capability epoch, benchmark ID, current lease rejection reason and planner decision.

### QS-02: Two models have compatible layer counts but different tokenizers

**Given** two stage manifests cover contiguous layers  
**and** their tokenizer or chat-template digests differ materially  
**When** an ingress constructs a pipeline  
**Then** planning fails with `manifest_incompatible` before any worker starts  
**and** no activation or token is sent.

**Current status:** target. Current code routes whole models and does not execute pipeline stages.

## 2. Request execution

### QS-03: A worker fails before first output

**Given** an admitted streaming request with remaining deadline and budget  
**and** no user-visible token has been emitted  
**When** a stage fails  
**Then** the ingress may replan within the same idempotency key  
**and** unused leases are released  
**and** the terminal receipt records both attempts.

### QS-04: A worker fails after first output

**Given** the client has received at least one generated token  
**When** a worker or network link fails  
**Then** the stream ends with a recoverable failure unless a supported checkpoint protocol exists  
**and** the ingress does not silently replay the request  
**and** the failure occurs before any duplicate side effect.

**Current status:** failure behavior is not yet fully tested for remote streaming.

### QS-05: Duplicate request delivery

**Given** a client retries a completed request with the same idempotency key and identical normalized input  
**When** the ingress receives the duplicate  
**Then** it returns the existing terminal state or attaches to the existing live request  
**and** no worker executes the request twice.

**Current status:** target. API idempotency keys are not yet implemented.

## 3. Membership and leases

### QS-06: A node is revoked during a request

**Given** an active worker lease under membership epoch `N`  
**When** membership epoch `N+1` revokes the node  
**Then** no new lease or commit from epoch `N` is accepted after the revocation boundary  
**and** the request reaches an explicit safe-retry or terminal state  
**and** the evidence retains both epochs.

### QS-07: Lease expires while a worker is paused

**Given** a paused worker holding lease fence `F`  
**When** the lease expires and another worker obtains fence `F+1`  
**Then** the old worker cannot commit  
**and** its late result is rejected or quarantined  
**and** only accepted work appears in accounting.

**Current status:** target.

## 4. Durable memory

### QS-08: Required remote replica is not acknowledged

**Given** a memory write requests D2 durability  
**and** the only remote storage attempt fails  
**When** the local commit succeeds  
**Then** the response reports `degraded`/D1 rather than D2  
**and** the replica manifest records no false acknowledgement  
**and** the repair queue schedules another compatible custodian.

### QS-09: A host loses its last local disk after D2 confirmation

**Given** a D2 memory with one acknowledged remote ciphertext copy and an accessible recovery key  
**When** the source host disk is destroyed  
**Then** an authorized recovery process locates the verified remote manifest  
**and** restores the exact committed version  
**and** the report states measured RPO/RTO and the key-custody assumptions.

**Current status:** remote ciphertext storage exists; automated key recovery and measured DR exercise do not.

### QS-10: A deleted memory exists on a stale replica

**Given** object version `V3` has a committed tombstone epoch `E7`  
**and** an offline custodian later returns version `V3`  
**When** anti-entropy compares the replica and tombstone epochs  
**Then** the stale object is deleted or inaccessible  
**and** it is never made searchable again  
**and** deletion debt remains visible until every known replica is resolved.

**Current status:** best-effort propagation only; no tombstone anti-entropy.

### QS-11: A namespace key is unavailable

**Given** encrypted memory exists at D2/D3  
**and** the active device key is unavailable  
**When** the owner attempts recovery  
**Then** the system requires an authorized recovery grant  
**and** does not substitute another namespace's key or report data recovered  
**and** the outcome is auditable.

**Current status:** no namespace key recovery architecture in the implementation.

## 5. Virtual roles

### QS-12: Old primary resumes after migration

**Given** a role migrated from primary epoch `E10` to target epoch `E11`  
**When** the old primary resumes with stale epoch `E10`  
**Then** it cannot accept new role actions or memory writes  
**and** its output is not treated as active state  
**and** an operator can inspect the epoch mismatch.

### QS-13: Migration fails after target preparation

**Given** a role has prepared a target but has not advanced the primary epoch  
**When** the target fails verification  
**Then** the original primary remains authoritative  
**and** the partially prepared target is deleted or quarantined  
**and** no user-visible split-brain occurs.

**Current status:** target; export/import exists, automatic two-phase migration and rollback do not.

## 6. Partition and offline behavior

### QS-14: An ingress loses contact with a domain catalog

**Given** an ingress has no current catalog snapshot  
**and** direct peer probes or another catalog replica are available  
**When** it plans a request  
**Then** it may use verified alternate discovery  
**and** it does not treat stale catalog capacity as a valid lease  
**and** it records a discovery degradation.

### QS-15: A node reconnects after an offline interval

**Given** an offline node with local memory/journal changes  
**When** it reconnects  
**Then** it obtains current membership and policy epochs before accepting remote work  
**and** reconciles tombstones and versions before advertising durability  
**and** does not duplicate committed requests or writes.

## 7. Security and abuse

### QS-16: A malicious peer advertises an internal URL

**Given** a peer announcement contains a loopback, link-local, metadata-service or disallowed redirect target  
**When** the node attempts to connect  
**Then** outbound policy rejects the destination before credentials are sent  
**and** an auditable security event is generated  
**and** other peers remain usable.

**Current status:** not implemented; the current HTTP mesh trusts advertised public URLs after signature checks.

### QS-17: A storage custodian is compromised

**Given** a custodian stores encrypted memory chunks  
**When** an attacker obtains its local database  
**Then** the attacker cannot decrypt namespace plaintext without owner key grants  
**and** tampered chunks fail digest/authentication checks  
**and** the namespace authority marks affected replicas degraded.

### QS-18: Poisoned memory attempts persistent prompt injection

**Given** untrusted content contains instructions aimed at changing durable policy  
**When** it enters the memory extraction pipeline  
**Then** it remains labeled as untrusted evidence  
**and** it cannot grant permissions or overwrite owner policy  
**and** promotion requires an explicit evidence gate.

**Current status:** target; the current memory API stores submitted text but no extraction/consolidation pipeline exists.

## 8. Continual learning

### QS-19: A local update improves training loss but regresses safety

**Given** a candidate adapter lowers its local training objective  
**When** the global compatibility, regression or safety suite fails  
**Then** the update is quarantined  
**and** no canary or production rollout occurs  
**and** the evaluation artifact remains available for investigation.

### QS-20: One participant submits a malformed or backdoored update

**Given** a training round with multiple participants  
**When** an update has invalid provenance, anomalous parameters or failed behavioral probes  
**Then** the aggregator excludes or isolates it according to the signed round policy  
**and** the round records the decision without claiming cryptographic proof of honesty.

**Current status:** design only.

## 9. Spatial action

### QS-21: A high-impact avatar action lacks a current grant

**Given** a role allowed to speak and gesture  
**When** a model proposes an action that changes shared world state without a valid short-lived action grant  
**Then** the adapter rejects the intent  
**and** logs the policy reason without storing raw sensor data  
**and** the role is not marked globally unsafe.

**Current status:** mock prefix-token permission exists; signed short-lived grants do not.

## 10. Release evidence

A PR or release note claiming a quality scenario must link:

- conformance test or benchmark;
- exact topology and versions;
- failure injection method;
- pass/fail criterion;
- residual failure boundary;
- raw or summarized artifact that can be reproduced.

Architecture acceptance does not imply production readiness; it only makes the next verification step explicit.
