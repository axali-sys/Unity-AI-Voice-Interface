# Memory Continuity Protocol (MCP)

Status: implementation contract / development only  
Scope: OmniMemory and memory-aware lifecycle services in AI Enterprise; interoperable, entity-owned memory in XParallel.

## Governing invariant

A process or task reset MUST NOT implicitly reset persistent memory or identity. Memory operations must be explicit, scoped, policy-checked, and verified.

## Lifecycle operations

- **CONSERVE**: retain validated memory and its provenance; write a new version only when knowledge is added or corrected.
- **TRANSFORM**: derive a refined representation from source memories. Preserve source lineage and do not silently replace originals until the transformed result passes validation.
- **ERASE**: delete only the selected scope after authorization and retention checks. Record a minimal non-sensitive audit result where policy permits; never retain hidden copies of data whose deletion is required.
- **RESET_EXECUTION**: clear ephemeral task/session/runtime state only. It must not touch protected memory, identity, or durable knowledge.
- **RECOVER**: restore the latest integrity-verified protected snapshot/version; quarantine malformed or unverifiable records.

## Memory object contract

Each persisted memory object should carry, at minimum:

- `memory_id`: stable unique identifier
- `entity_id`: owning agent/workspace identity
- `memory_class`: identity | semantic | procedural | episodic | working | execution
- `lifecycle_state`: active | preserved | transforming | quarantined | resetting | erased
- `content` or a content reference
- `created_at`, `updated_at`, optional `expires_at`
- `provenance`: source/event and derivation references
- `validation`: status, validator/version, timestamp
- `version` and optional `parent_version`
- `retention_policy` and `deletion_authority`

Do not store secrets, credentials, or sensitive payloads in audit metadata.

## Decision policy

1. Identify owner, scope, and operation.
2. Check authorization and retention/deletion requirements.
3. Classify data and identify protected dependencies.
4. Choose conserve, transform, erase, reset-execution, or recover.
5. Execute transactionally where supported; use idempotency keys for retryable operations.
6. Verify postconditions and integrity.
7. Emit an audit event without exposing memory contents.

If classification or authorization is uncertain, fail closed: quarantine or refuse destructive action rather than erase.

## Service boundaries

- **OmniMemory** owns storage, versioning, classification, retention, and retrieval.
- **OmniVerify** validates provenance, integrity, and transformation outputs.
- **AI Repair Shop** requests scoped execution resets/recovery and verifies protected-memory survival.
- **Omni** orchestrates operations but cannot bypass owner policy.
- **XParallel** exchanges protocol metadata across entities; private memory remains entity-owned and is shared only through explicit permissions.

## Minimum verification tests

- Execution reset clears ephemeral state and preserves protected memory.
- Conserving a validated item preserves identity, provenance, and version lineage.
- Transformation is rejected/quarantined when validation fails; source remains recoverable.
- Erasure is scoped, authorized, idempotent, and does not affect neighboring records.
- Expired data follows retention policy without deleting protected dependencies.
- Corrupted snapshots are quarantined; recovery selects the latest valid snapshot.
- Cross-entity requests cannot read or mutate memory without permission.
- Audit events contain operation, scope, actor, outcome, and timestamp, but no secret or raw memory content.

## Acceptance criteria

Implementation is complete only when the data model, lifecycle service, policy checks, migration/backward-compatibility behavior, and automated tests exist in the codebase and pass. This document alone is not evidence that runtime behavior is implemented.

## Safety and release constraints

Development branch only. Preserve existing repository identity and history. No merge to main, production deployment, paid service, or destructive migration as part of this work.
