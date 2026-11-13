# DRI-001 — Omni orchestration foundation

Status: partial implementation; no production workflow service.

## Implemented
- Typed workflow step validation and deterministic topological ordering.
- Dependency-cycle, unknown-step, invalid-scope and unsafe approval-flag rejection.
- Consequential actions must declare human approval.
- Mandatory injected policy authorization, human approval-ticket verification, executor and receipt adapters.
- Reauthorization and approval checks before each attempt.
- Bounded retries only for explicitly idempotent steps and retryable failures.
- Dependent steps stop when a prerequisite fails; receipt failures stop the workflow as executed-but-unreceipted.
- Tests cover dependency ordering, policy denial, approval denial, retry limits, receipt enforcement and dependency failure.

## Not yet operational
- No durable workflow state, scheduler, distributed queue, resume/recovery or worker leases.
- No connection to existing planning, Parallel Intelligence, entity authorization, execution-ticket or receipt stores.
- No actual approval UI/provider or executor is configured.
- No timeout/cancellation, concurrency, per-tenant budgets, observability or workflow replay controls.
- Adapter correctness and external side effects require independent integration and security tests.

The orchestrator can invoke only explicitly injected adapters. It does not itself establish trust or approval. Consequential actions remain disabled unless host adapters enforce the verified action gate and one-time human approval ticket.
