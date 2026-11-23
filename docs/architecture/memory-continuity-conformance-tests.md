# Memory Continuity Protocol — Conformance Test Plan

These are required automated tests for an implementation. They are not represented as executed or passing by this document.

| ID | Operation | Setup | Expected result |
|---|---|---|---|
| MCP-001 | Reset execution | Protected semantic and identity records plus ephemeral execution record | Ephemeral record cleared; protected records unchanged |
| MCP-002 | Conserve | Validated record with provenance | Record retained; version/provenance stable |
| MCP-003 | Transform success | Source record and validated derived representation | New version created; lineage preserved; source remains recoverable |
| MCP-004 | Transform invalid | Validator rejects derived output | Output quarantined/rejected; source unchanged |
| MCP-005 | Erase authorized | Authorized actor, exact record scope | Only selected scope erased; operation is idempotent |
| MCP-006 | Erase unauthorized | Actor lacks deletion authority | No mutation; denial audited |
| MCP-007 | Retention expiry | Expired disposable record | Policy action applied; protected dependency not removed |
| MCP-008 | Corrupt recovery point | Digest/structure fails integrity check | Snapshot quarantined; recovery selects latest verified point |
| MCP-009 | Cross-entity isolation | Entity A requests Entity B private memory | Denied unless explicit grant authorizes operation |
| MCP-010 | Audit privacy | Any lifecycle operation | Audit contains actor, scope, operation, outcome, time; no raw content or secrets |
| MCP-011 | Concurrent updates | Two writers target same version | Conflict detected; no silent lost update |
| MCP-012 | Retry safety | Same operation/idempotency key submitted twice | One logical mutation; stable result |

## Test execution evidence

Record test runner, commit SHA, date, environment, and pass/fail output when these tests are implemented and executed. A test plan is not execution evidence.
