# OneAI five foundational milestones — delivery and verification

This document distinguishes implemented code from capability that is not yet integrated or proven.

## 1. ƎllE Intelligence Architecture
Service-layer task model and guarded lifecycle are in `xparallel/elle_lifecycle.py`. It stores objective, expected outcome, workspace, owner, constraints, knowledge references, capabilities, risk, state, approval and verification. High/critical tasks require an explicit approval record. The service does not run arbitrary code.

## 2. Omni Knowledge Genome
`xparallel/omni_genome.py` stores workspace-scoped records, source references, immutable version rows, verification evidence and audit events in SQLite. Records start received/unverified. Search is workspace-scoped. Model-origin records are not automatically verified.

## 3. Parallel Intelligence Protocol
`xparallel/parallel_intelligence.py` reuses the configured provider catalogue and existing provider-backed planner. It deliberately reports single-provider planning and says multi-model consensus is unavailable. It does not fabricate panel results. A generic provider invocation adapter and independent model comparison remain future work.

## 4. XParallel Interoperability Protocol
`xparallel/interoperability_protocol.py` maps registered roaming runtimes to public agent passports and routes allowlisted task types through the existing authenticated task queue. Dispatch requires an approval flag from a trusted backend caller. Runtime registration, heartbeat, claim and completion remain in the existing registry.

## 5. AROT Evidence Protocol
`xparallel/arot_evidence.py` maps task/knowledge events to the existing SQLite audit repository. Existing audit events remain the system-of-record ledger; the adapter adds entity and event references.

## HTTP integration
Authenticated API routes are mounted in the existing `xparallel/server.py`. They use the existing bearer-token gate and workspace context. The present repository has a shared service token and a caller-supplied workspace ID; it does not yet provide per-user workspace membership or identity-bound authorization. Therefore these endpoints are suitable for controlled development integration, not a claim of multi-tenant production isolation.

## Verification status
The tests in `tests/test_omni_genome.py` and `tests/test_elle_lifecycle.py` are committed but must be run by CI or in a Python 3.12 environment. No runtime or production verification is implied by a commit. Parallel multi-model consensus is explicitly not implemented. UI integration, per-user authentication, retention/deletion workflows and operational deployment verification remain open.
