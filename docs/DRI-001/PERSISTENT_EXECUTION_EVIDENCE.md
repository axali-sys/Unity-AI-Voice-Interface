# Persistent execution evidence store

## Implementation

`xparallel/execution_evidence_store.py` adds a workspace-scoped SQLite
evidence store with:
- canonical JSON serialization and SHA-256 content addressing;
- WAL mode and SQLite `synchronous=FULL` commits;
- append-only update/delete triggers;
- explicit result sanitization before persistence;
- authenticated, workspace-bound reads with a separate read authorization
  callback;
- integrity verification on every read.

The store can be injected into `ExecutionHostServices` as its
`store_evidence` adapter. The host must supply the trusted principal and
intent workspace identifiers. The adapter returns content-addressed evidence
references suitable for inclusion in an execution receipt.

## Important limitations

This is persistent local SQLite storage, not a managed durable object store.
Durability depends on the host's mounted persistent volume, backup policy,
filesystem guarantees and recovery testing. SQLite evidence is not encrypted
at rest by this module and is not externally anchored. The mandatory sanitizer
must remove secrets and sensitive output before storage.

This milestone does not implement CPU, memory or PID measurement from the
actual Docker cgroup. The runner currently reports output bytes but not trusted
host-level resource measurements. The host service must continue to reject
incomplete measurements. It also does not enable a private HTTP execution
route or constitute production readiness.

## Verification

Run `python -m unittest tests.test_execution_evidence_store -v`.
