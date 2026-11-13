# DRI-001 — Cognitive runtime and model gateway foundation

Status: partial implementation.

## Implemented
- Provider-neutral model gateway with explicit adapter registration and selection.
- Local-first default when an Ollama adapter is configured; no paid provider is selected implicitly.
- Optional Ollama HTTP adapter restricted to loopback hosts.
- Message validation and bounded context/output budgets.
- Structured JSON output parsing with a bounded schema-validation subset.
- Tool contract registration and input validation; tool proposals require an injected authorization decision.
- Tool calls remain proposal-only; no tool is executed by this runtime.
- Deterministic evaluation harness with pass/fail counts and pass rate.
- Tests cover provider selection, budgets, structured output, tool authorization, evaluation and Ollama loopback restrictions.

## Not yet operational
- No live local model was started or queried; the Ollama adapter is mock-tested only.
- Existing chat_service.py routes are not migrated to this gateway.
- No production model policy, per-tenant model allowlist, streaming, cancellation, token accounting or context summarization.
- No verified action gate / approval-ticket / receipt integration for actual tool execution.
- No benchmark dataset, quality evaluation, latency/cost monitoring or independent prompt-injection review.
- No model weights are bundled and no paid provider is configured by this change.

Model output is untrusted. Structured output validity is not proof of factual correctness. Tool proposals are not executions. Consequential actions must remain behind the existing server-side authorization and human approval boundaries.
