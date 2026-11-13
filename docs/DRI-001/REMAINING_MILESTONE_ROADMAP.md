# DRI-001 — Remaining Milestone Roadmap

Status: living engineering plan; milestone acceptance is evidence-based. This roadmap does not authorize merge, production deployment, paid services, or changes to independent products.

## Completed foundations

- M1: architecture baseline, repository/prototype audit, 113-component and 15-preservation-identity coverage snapshot.
- M2.1–M2.8: Digital DNA schema/registry prototype, Ed25519 identity and key lifecycle, deny-by-default action policy, signed message envelopes, local policy-gated message gateway, governance/permission registry, capability verification laboratory.
- M2.9: verified entity action gate composing trusted identity context, exact artifact-bound capability evidence, and approved exact-scope grants. The gate decides only; it does not execute.
- M2.10: restricted Docker execution-boundary hardening is implemented in the isolated branch. Final CI rerun after the last test-fixture correction remains pending; no live Docker hostile-code test has been performed.

## Remaining milestones and acceptance gates

### M2.11 — Trusted host adapters and enforcement boundary
Implement concrete adapters for authentication, entity/key/capability lookup, governance grants, evidence store and policy decisions. Ensure all identity/workspace values come from server-side verification, not request-body claims. Add route-level integration tests. Do not enable consequential execution until each adapter is independently reviewed.

### M2.12 — Execution approval, job lifecycle and revocation
Add immutable job intents, explicit human approval bound to exact artifact/action/resource/limits, one-time execution tickets, expiry, cancellation, revocation checks immediately before start and during execution, and terminal outcomes. Approval must not be transferable to a different payload.

### M2.13 — Execution evidence and provenance
Record signed job receipts, input/output digests, runner image digest, policy decision, approvals, timestamps, resource usage, exit status and evidence references. Add tamper-evident chaining and external anchoring design; do not call local SQLite audit immutable.

### M2.14 — Durable storage and recovery
Move registry, grants, queues, verification runs and job state behind repository interfaces with transactional semantics, backup/restore, migrations, retention and recovery tests. SQLite remains a local development option; distributed use requires a reviewed durable backend.

### M2.15 — Secure network transport and distributed messaging
Add authenticated encrypted transport, schema negotiation, message acknowledgement, bounded retries, dead-letter handling, idempotency, rate limits, per-entity quotas, revocation propagation and multi-node tests. The current local pull queue is not a distributed message fabric.

### M2.16 — Entity discovery and federation
Implement public/private discovery, signed registry records, capability query and compatibility negotiation, owner-controlled visibility, federation trust policies, anti-enumeration controls and independent registry conformance tests.

### M3.1 — Entity memory and knowledge provenance
Build permission-aware memory scopes, provenance, retention, export/deletion, encrypted storage design, retrieval evaluation and workspace/entity isolation. Do not store credentials in model memory.

### M3.2 — Cognitive runtime and model gateway
Create provider-neutral runtime adapters, tool contracts, context budgets, model selection, structured outputs, failure handling and evaluation harnesses. Provider credentials remain server-side and optional; zero-cost/local mode must remain viable.

### M3.3 — Parallel Intelligence collaboration
Implement bounded specialist delegation, attributable contributions, independent verification, disagreement resolution, synthesis, budgets and human approval. Measure task quality rather than treating agent count as intelligence.

### M3.4 — Omni orchestration
Connect planning, scheduling, routing, retries, policy checks, approval gates and execution receipts through typed workflows. Every external or consequential action must use the same server-side enforcement boundary.

### M3.5 — Parallel Verse persistent environments
Integrate workspace-scoped spaces, entities, conversations, tasks and event histories with durable storage, access control, lifecycle management and multi-entity isolation. The existing SQLite/optional PostgreSQL prototype is not yet a deployed persistent universe.

### M3.6 — Interoperability and developer conformance kit
Publish versioned SDKs, reference clients, test vectors, protocol compatibility rules, sandboxed sample entities, conformance tests and migration policy. Demonstrate that an independently authored entity can register, communicate and collaborate under the same governance rules.

### M4.1 — Evolution and learning laboratory
Add evaluation datasets, reproducible experiments, versioned proposals, human review, staged rollout, rollback, regression detection and provenance. No autonomous self-modification or silent capability promotion.

### M4.2 — Reality interface
Design permissioned connectors to external services and devices with explicit scopes, operator consent, safety interlocks, simulation-first testing and emergency revocation. Physical-world actions remain disabled until independent safety validation.

### M5 — System integration and independent security validation
Integrate components behind stable interfaces, perform threat modeling, dependency and supply-chain review, penetration testing, disaster recovery, privacy review, accessibility checks, performance and load tests, and independent conformance review. Resolve all critical/high findings before any release proposal.

### M6 — Release-readiness dossier
Produce a component-by-component evidence register, operational runbooks, cost and hosting analysis, backup/restore proof, incident response, governance terms, user documentation, API compatibility guarantees and explicit release blockers. A release recommendation is not a deployment authorization.

## Cross-cutting completion rules

- Keep all work on isolated development branches; do not merge to main.
- No production deployment, domain/DNS change, purchase, paid service, or external commitment without separate explicit approval.
- Keep NexAI and IDEAS independent.
- Preserve existing repositories, histories, identities, routes and integrations.
- Mark every capability as verified, partial, experimental, documented-only, blocked, or unverified based on observable evidence.
- Do not equate passing unit tests with production readiness, safety, general intelligence, or consciousness.
- A milestone is complete only when its code, documentation, tests, CI evidence, limitations and acceptance criteria are all recorded.
