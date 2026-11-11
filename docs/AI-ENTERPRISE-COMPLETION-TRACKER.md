# AI Enterprise — Completion Execution Tracker

**Product name:** AI  
**Public domain intent:** `axaliai.com` (domain managed through Squarespace)  
**Primary repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Integration branch:** `enterprise/axaliai-completion`  
**Independent identity adapter:** `axali-sys/nexai-platform` / `integration/axaliai-nexai-identity`

## Owner constraints

This tracker implements the owner's 2026-11-11 authorization:
- Development work only on isolated branches.
- Zero-cost only; no purchases, paid services, or paid commitments.
- No merge to `main`/`master`, no production deployment, and no production configuration changes.
- Preserve existing repositories, Git histories, routes, integrations and product identities.
- NexAI and IDEAS remain independent products. NexAI may provide optional identity through a versioned adapter; it does not transfer its users, sessions, database, runtime or ownership to AI.
- Never expose secrets in browser code, source control, logs or URLs.
- A design, branch, passing unit test or component name is not proof of an operational capability.

## Domain and preview decision

The owner has selected `axaliai.com` as the public domain intent and Squarespace as the domain-management platform. The current application preview URL is intentionally not required for this development programme.

Until the actual application origin is known:
- Do not configure an SSO callback or allow-list using a guessed URL.
- Do not change Squarespace DNS, Vercel domains, Render services or production settings.
- Build and test the identity protocol locally with explicit test origins and test redirect allow-lists.
- Keep the final browser callback/domain binding as a release configuration task after the application host and canonical origin are confirmed.
- Treat the public Squarespace website and the AI application runtime as separate until hosting is verified.

## Baseline already present (not a completion claim)

### AI Enterprise branch
- Signed tenant identity token primitive and issuer/audience verification.
- Role/action authorization middleware on selected ƎllE, Omni, Parallel Research and XParallel user APIs.
- Separation of human identity from `XP_TOKEN` machine/service authentication.
- Local Ollama-first chat routing and fail-closed provider-unavailable behavior.
- Unauthenticated preview chat isolated to a non-personal preview workspace with memory disabled.
- Focused authorization, tenant-isolation and zero-cost chat tests.
- Draft PR #61 and successful XParallel CI runs #153 and #157, as recorded in the branch documentation.

### NexAI independent branch
- Authenticated NexAI session and NexAI-owned workspace membership checks.
- Optional short-lived identity assertion endpoint with issuer `nexai-platform` and audience `axaliai-enterprise`.
- Dedicated shared-secret configuration, disabled by default.
- Draft PR #1 and successful NexAI CI run #52, as recorded in its PR.

These are foundations only. The NexAI SSO server protocol exists, but browser consent UI and AI Enterprise callback/session handoff, actual hosted inference, complete memory lifecycle, full 113-component audit and release evidence remain outstanding.

## Dependency-ordered completion milestones

### M0 — Repository reconciliation and baseline inventory
**Status:** In progress / evidence gathering.

- Inspect default/development branches, open and closed PRs, commit ancestry and all integration branches.
- Map frontend routes, API routes, services, schemas, databases, authentication, queues, audit, provider gateway, deployment configuration and tests.
- Reconcile the existing ƎllE/Omni, XParallel, AI Mixer, Build Studio, Repair Shop and website work without replacing the existing application.
- Identify duplicate implementations and assign one authoritative owner per responsibility.
- Produce file-level changes, dependency map, migration notes and rollback plan.

**Exit evidence:** reviewed repository map, duplicate/conflict register, route/service ownership matrix and agreed development baseline.

### M1 — Identity, sessions and workspace security
**Status:** Partial; NexAI authorization-code protocol implemented, enterprise browser handoff outstanding.

- Complete a first-party AI login/session and authoritative workspace membership path, or integrate an approved independent provider through an adapter.
- Connect the NexAI authorization-code + PKCE protocol to an enterprise callback, server-to-server code exchange and AI-owned session creation; retain exact redirect allow-list, state validation, explicit consent and replay prevention.
- Do not place bearer tokens in query strings, localStorage or browser-readable persistent storage.
- Enforce authentication, membership, role, workspace isolation and revocation on every user-facing API route.
- Keep service credentials separate from human identity.
- Add session expiry, CSRF protections, secure cookie settings, rate limits and audit events.

**Exit evidence:** NexAI API protocol tests pass; remaining browser/API integration tests must cover login, logout, consent UI, state, expiry, replay, revoked membership, cross-workspace denial and privilege escalation. The final callback origin is configured only after the actual application host is confirmed.

### M2 — Core runtime and provider gateway
**Status:** Partial; live host inference unverified.

- Verify the existing chat path end-to-end from UI → server API → XParallel → model adapter → response.
- Prove local Ollama inference from the actual backend host; do not assume a phone can host the model or that a cloud host has Ollama installed.
- Keep open-source/local inference first and paid providers disabled by default.
- Implement provider capability/health checks, timeouts, cancellation, bounded retries, safe fallback and explicit unavailable states.
- Keep AI Mixer as the user-facing selection/comparison experience and Model Gateway as the provider-neutral backend.
- Redact credentials and sensitive prompts from logs.

**Exit evidence:** real inference smoke test from the backend host, provider contract suite, timeout/failure tests and verified zero-cost routing behavior.

### M3 — Omni knowledge, memory and data lifecycle
**Status:** Partial; lifecycle/recovery incomplete.

- Inventory existing SQLite memory, conversation, Omni knowledge, repair and task stores before changing schemas.
- Define canonical ownership and stable identifiers; avoid creating competing memory databases.
- Implement tenant/workspace-scoped records, provenance, source metadata, version history and access checks.
- Define ingestion, normalization, indexing, retrieval, ranking, freshness and conflict handling.
- Add correction, user export, deletion, retention, backup, restore and migration behavior.
- Ensure retrieval filters permissions before ranking or returning content.
- Keep lexical retrieval distinct from semantic/vector retrieval; do not claim embeddings are active unless an embedding model is actually configured and tested.

**Exit evidence:** create/read/update/delete/export/backup/restore tests, tenant isolation, retrieval relevance tests, provenance checks and a successful restore drill.

### M4 — ƎllE intelligence and Parallel Intelligence
**Status:** Partial; capability-level evidence audit required.

- Complete task lifecycle: understand → plan → research → build → test → approve → execute → verify → remember.
- Persist task state and evidence with owner/workspace boundaries.
- Attribute each model/agent contribution; show disagreement and uncertainty rather than fabricating consensus.
- Separate answer self-evaluation, artifact verification and AROT evidence recording.
- Add bounded context selection, knowledge-gap detection, citations/provenance and safe abstention.
- Keep external actions approval-gated and make dry-run behavior side-effect free.

**Exit evidence:** reproducible task tests, attributed multi-model tests where multiple configured models are available, evaluation benchmarks, approval denial tests and artifact verification records.

### M5 — Omni orchestration and XParallel execution
**Status:** Existing foundations require source-to-runtime verification.

- Audit registry, worker registration, heartbeat, task claim, lease, result, revoke and failure lifecycle.
- Verify queue durability, idempotency, retries, dead-letter handling and recovery.
- Define versioned event/task/agent manifests and compatibility tests.
- Enforce least privilege, sandboxing, egress restrictions, quotas, approvals and audit.
- Verify Parallel Verse persistence and tenant boundaries before describing it as operational.
- Keep roaming workers opt-in and unable to execute arbitrary host commands.

**Exit evidence:** lifecycle integration tests, worker-loss recovery, duplicate-delivery tests, sandbox/egress tests, revocation tests and traceable execution evidence.

### M6 — 113-component and 15-identity reconciliation
**Status:** Register exists; full audit not complete.

For every C001–C113 and P001–P015:
- Inspect implementation paths, call sites, contracts, dependencies and tests.
- Record the authoritative owner, shared implementation, data classification, tenant boundary and cost profile.
- Assign one evidence-backed status: Existing and verified, Partial, Planned, Experimental or Blocked.
- Record acceptance tests and runtime evidence; distinguish code presence from a reachable, functioning feature.
- Preserve every source name and all 15 existing product identities even when capabilities share infrastructure.
- Resolve overlap without silently deleting or double-counting capabilities.

**Exit evidence:** complete traceability matrix with repository paths, test outcomes, evidence links and remaining work for all 128 entries. Experimental entries remain explicitly experimental unless independently validated.

### M7 — Independent product adapters
**Status:** NexAI identity assertion foundation exists; IDEAS audit pending.

- Keep NexAI and IDEAS as separate products and repositories.
- Define versioned, permission-scoped adapter contracts for any optional connection.
- NexAI integration must use its own authentication and membership authority; AI must never access NexAI passwords, session cookies or database directly.
- Inspect IDEAS repository and define an adapter only after its own security and API audit.
- Preserve independent deployment, data ownership and ability to revoke integrations.

**Exit evidence:** contract tests, authentication and revocation tests, data-boundary tests and independent product owners documented.

### M8 — Mobile-first command center and creation workflows
**Status:** Existing UI requires route-by-route audit.

- Inspect existing mobile UI before redesigning or replacing it.
- Integrate truthful status for assistant, tasks, memory, provider health, agents and approvals.
- Connect Build Studio, QCode, AI Repair Shop and AI Mixer to real backend contracts.
- Ensure controls show unavailable/blocked states rather than demo success.
- Provide accessible navigation, low-bandwidth behavior, recoverable errors and clear confirmation before consequential actions.

**Exit evidence:** mobile viewport tests, keyboard/accessibility checks, UI-to-API integration tests and no fabricated operational states.

### M9 — Governance, observability and release verification
**Status:** Partial; full hardening outstanding.

- Verify AROT audit integrity, correlation IDs, event lineage and secret redaction.
- Add resource limits, abuse controls, retention policies, incident and recovery runbooks.
- Run security review, dependency review, fault injection and restore drills.
- Execute the full unit, contract, integration, tenant-isolation and browser test matrix.
- Produce a release dossier listing verified features, partial features, blocked features, test runs, known risks, cost assumptions and rollback steps.
- Keep all release gates closed until owner approval.

**Exit evidence:** reproducible green test matrix, security findings disposition, recovery evidence, complete component traceability and signed-off release dossier.

## Immediate execution order

1. Finish M0 repository reconciliation and identify the next highest-risk code gap.
2. Implement M1 identity/session protocol locally without a production callback URL.
3. In parallel, audit M2 chat/provider runtime and M3 existing memory stores before modifying them.
4. Continue M4/M5 only after identity, persistence and execution contracts are stable.
5. Audit C001–C113 and P001–P015 continuously; do not defer all evidence work until the end.
6. Complete M7/M8/M9 and prepare a release dossier. Do not merge or deploy.

## Current blockers and deferred items

- Final SSO redirect allow-list and callback domain: deferred until the actual application origin is known; this does not block local protocol implementation.
- Shared NexAI/AI identity secret: not generated or configured; keep the optional integration disabled.
- Hosted Ollama: no free compute is assumed provisioned. Live inference remains blocked until a reachable, user-authorized host exists.
- IDEAS: independent repository audit and interface contract remain outstanding.
- Squarespace DNS/domain connection: not part of development completion and must not be changed without explicit authorization.
- Production release: prohibited by the current authorization.

## Reporting format for every milestone

Record: branch and commit; files changed; behavior implemented; tests run and exact outcomes; CI run/link; runtime evidence; security and tenant boundaries; costs; blockers; rollback notes; and the next milestone. Never report success for an action that was not actually executed and verified.
