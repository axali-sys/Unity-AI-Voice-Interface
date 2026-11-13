# DRI-001 — Parallel Intelligence collaboration foundation

Status: partial implementation.

## Implemented
- Bounded specialist selection (maximum five) with deterministic sequential invocation.
- Attributed contributions, evidence references and SHA-256 content digests.
- Mandatory separate verifier adapter; verifier failures become inconclusive.
- Only independently verified contributions reach the synthesis adapter.
- Conflicts and unverified contributions force human review.
- Strict task/context/per-specialist/aggregate output budgets.
- No tool execution, external action or autonomous approval.
- Tests cover attribution, synthesis, verifier rejection/failure, conflict escalation and budgets.

## Not yet operational
- No specialist models are connected to this coordinator.
- No durable task queue, concurrency scheduler, timeout/cancellation or cost/token budget accounting.
- No calibrated disagreement detection; conflict reporting is supplied by the synthesis adapter.
- No evidence-source validation service, benchmark dataset, task-quality scoring or audit integration.
- No human review UI, approval-ticket binding or verified execution integration.
- No multi-tenant production integration or independent safety review.

Agent count is not an intelligence metric. The coordinator records contribution and verification status; it does not establish truth, general intelligence or consciousness.
