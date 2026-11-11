# Coordinated AI Enterprise and 113-Component Delivery Programme

## Owner authorization (2026-11-11)
This programme is authorized for coordinated development only. It must remain zero-cost, isolated from production, and preserve every existing repository, product identity, route, integration, and Git history. No default-branch merge, production deployment/configuration change, paid service, purchase, token issuance, or irreversible external action is authorized.

## Product and repository boundaries
- AXALIAI / AI Enterprise: umbrella infrastructure and coordination programme in `axali-sys/Unity-AI-Voice-Interface`.
- ƎllE: primary intelligence interface/runtime; not a replacement for independent products.
- Omni: knowledge plane and orchestration capabilities with distinct contracts.
- XParallel: interoperability, roaming, registry, task transport and controlled execution infrastructure.
- Parallel Intelligence: attributed multi-model/agent collaboration and evaluation.
- NexAI: independent AI assistant platform in `axali-sys/nexai-platform`; integration only through explicit versioned APIs/adapters. Its auth, memory, workspace and model gateway remain owned by NexAI.
- IDEAS: independent platform in `axali-sys/ideas-platform-`; no absorption or identity change. Integration only after its own repository audit and explicit interface contract.
- Other existing identities (UnitAI, Omnibox, Jellybox, UIDaaS, VOUCHER, WFAIAI OS, QCode, Build Studio, AI Repair Shop, AI Mixer, AROT) remain traceable and retain ownership boundaries.

## Existing work discovered (not a completeness claim)
Primary repository:
- Draft PR #59 contains a ƎllE lifecycle, Omni knowledge-genome, Parallel Intelligence, XParallel roaming and AROT foundation. Its PR description records outstanding auth/membership enforcement, UI integration, backup/restore, retention/deletion, concurrency and live-provider verification.
- Draft PR #58 contains the 113-entry register and 15 separate preservation identities. All 113 entries are initially Unverified except six explicitly marked Experimental; code-level evidence audit is still required.
- Draft PR #60 contains the Axaliai infrastructure website and explicitly disables chat until trusted user authentication/workspace authorization are available.
- Draft PR #61 adds a short-lived HS256 tenant identity primitive and tests. CI run for its current head reports success. This is not complete authentication or route authorization; do not expose tenant APIs until a trusted login adapter and membership enforcement exist.
- Existing merged XParallel work includes security foundations, task queue, roaming worker, storage/persistence and related tests. Re-audit exact behavior before reuse.
NexAI:
- Active branch is `development`; it has its own FastAPI/Next.js app, account/workspace authorization, SQLite persistence, memory retrieval/proposals and an optional Ollama adapter.
- README explicitly states hosted Ollama is not provisioned, semantic retrieval is not implemented (current retrieval is lexical), and several security/product hardening tasks remain.
IDEAS:
- Repository `axali-sys/ideas-platform-` has `main` and `release/milestone-9-deployment-prep`; no pull requests were returned by the repository PR search. Its implementation must be audited independently before any adapter is proposed.

## Delivery method
Maintain a traceability matrix for C001-C113 and P001-P015. For each entry record owner, repository/path, dependencies, API/event contract, data classification, tenant boundary, status (Existing and verified / Partial / Planned / Experimental / Blocked), tests, test result, runtime evidence, cost profile and remaining work. A branch name, design document or green unrelated test is not implementation evidence.

### Phase 0 — Reconciliation and baseline
- Inspect default and development branches, all relevant open/closed PRs, commit ancestry, routes, schemas, data stores, auth, provider adapters, queues, audit, CI and deployment configuration.
- Detect duplicate implementations and choose one authoritative owner per responsibility.
- Reconcile the 113 register against source code and tests without deleting overlapping source names.
- Produce a file-by-file integration plan and migration/rollback notes.

### Phase 1 — Security and runtime foundation
- Trusted login adapter, server-derived actor/workspace, membership checks and route-level authorization.
- UIDaaS, Permission Engine, Policy Engine, Credential Vault, API Gateway, Model Gateway.
- Shared event/queue contracts, idempotency, rate/resource limits, audit and secret redaction.
- Deny-by-default; no browser-supplied identity, role, workspace or approval claims.

### Phase 2 — Omni knowledge plane
- Authorized connectors and OmniStream ingestion.
- Normalize, validate, classify, version and persist with workspace scoping.
- OmniMemory, OmniGraph/Knowledge Genome, OmniIndex, OmniSearch, OmniTrace, OmniArchive, OmniSync and OmniPulse.
- Explicit provenance, correction, export, deletion, retention, backup and restore.

### Phase 3 — Intelligence and evaluation
- ƎllE task lifecycle and context integration.
- Model Gateway and AI Mixer separation; provider availability must be real and transparent.
- Parallel Intelligence with attributed outputs, disagreement visibility and no fabricated consensus.
- Self-Evaluation, explainability, confidence/uncertainty, knowledge-gap detection and OmniVerify.

### Phase 4 — Orchestration and XParallel
- OmniPlan, OmniFlow, Scheduler, Control, Event, Sim, Recovery and Swarm.
- Agent Registry, Passport, XParallel Protocol/Connect/Discovery/Exchange/Roaming/Mesh/Sandbox and Parallel Verse.
- Explicit human approval for consequential actions; sandboxed, allowlisted execution only.

### Phase 5 — Creation, domain and organizational capabilities
- Build Studio, QCode, media workflows, website/app generation, AI Repair Shop.
- Engineering, thermal, industrial, scientific, geospatial, energy, agricultural and digital-twin capability packs.
- Organizational/personal assistants with data access controls and truthful capability boundaries.

### Phase 6 — Experimental systems and hardening
- World Model, Parallel Reality, Time Intelligence and governed independent-agent network remain experimental until validated.
- Mobile/low-bandwidth behavior, accessibility, fault injection, restore drills, security review and operational runbooks.

## Non-negotiable acceptance gates
1. Unit and contract tests pass for changed code.
2. Integration tests prove real route-to-service behavior, not only isolated helper functions.
3. Tenant/workspace isolation tests prove cross-workspace denial.
4. Secret, approval and egress boundaries are tested.
5. Data lifecycle (create/read/update/delete/export/backup/restore) is verified where applicable.
6. Provider claims are backed by a real configured runtime test; otherwise report unavailable.
7. Each component is marked implemented only with code, tests and relevant runtime evidence.
8. Keep work on isolated branches and draft PRs targeting development branches only. Never merge to main/master or deploy production.

## Immediate blockers and honesty rules
- PR #61 identity tokens are a primitive only; a trusted upstream login and membership lookup are still required.
- PR #59 service foundations are not yet proven as authenticated end-to-end UI workflows.
- NexAI's Ollama hosting configuration does not provision compute or download/run a model until a suitable host is explicitly available.
- IDEAS has not yet been inspected beyond repository/branch/PR metadata.
- Zero-cost means no hosted inference or cloud compute is assumed available. Local inference requires user-owned hardware; optional external providers remain disabled unless already configured and approved.
- Report exact changed files, commits, CI run URLs/status, test coverage, blockers and what was not done. Never claim production readiness from CI alone.
