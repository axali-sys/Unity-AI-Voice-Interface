# Axaliai AI Enterprise — Repository Integration Plan

**Status:** Planning baseline only  
**Created:** 2026-11-10  
**Base:** `main` at the integration-plan branch creation point  
**Scope:** Read-only assessment converted into a file-level implementation plan  
**Safety:** This document does not authorize merging PRs, changing production, configuring paid services, or exposing secrets.

## 1. Enterprise ownership model

| Capability | System of record / owner | Integration rule |
|---|---|---|
| Enterprise identity and public portal | Axaliai | Umbrella identity; do not absorb independent product identities |
| Assistant experience and task lifecycle | ƎllE | UI and task orchestration; server-side calls only |
| Interoperability, execution and roaming workers | XParallel | Existing authenticated service boundary; approval before consequential execution |
| Knowledge records, versions and evidence | Omni Genome | Knowledge record/version source of truth |
| Learning, memory ranking and adaptation | AILLM | Service layer over existing memory and Omni stores; no third competing database |
| Multi-model collaboration | Parallel Intelligence | Model gateway and comparison; no fabricated consensus |
| Workspace shell | OneAI Workspace | Client experience; connect through versioned backend APIs |
| Independent AI product | NexAI | Separate identity, auth, memory and release lifecycle; optional adapters only |
| Global idea marketplace | IDEAS | Separate product and commercial domain |
| Specialized products | UnitAI, Omnibox, Jellybox, Build Studio, AI Repair Shop, Parallel Verse | Own modules/products connected by explicit contracts |

## 2. Pull-request dependency and reconciliation plan

Current inspected state: PRs #48, #49, #59 and #60 are open draft PRs. PR #48 and PR #59 target `main`; PR #49 targets PR #48's head branch; PR #60 targets `main`. Do not merge these independently without a fresh diff and test review.

1. Compare PR #48 against `main`; preserve deterministic local-first routing, explicit free-fallback policy and secret-safe provider catalogue.
2. Compare PR #49 against PR #48; retain authenticated ƎllE → XParallel `/chat` routing and truthful upstream errors. Confirm whether its assumptions still match current server/API code.
3. Compare PR #59 against `main` and against the combined #48/#49 result. Reconcile task lifecycle, Omni Genome, Parallel Intelligence, roaming dispatch and AROT without duplicating existing services.
4. Compare PR #60 against the final application integration candidate. Preserve `/assistant` and `/api/chat`; do not publish endpoints as operational unless runtime-tested.
5. Keep PR #58's 113-component register as the portfolio inventory input, but validate each status against code, tests and deployment evidence.
6. Do not retarget, close, approve or merge any existing PR as part of this planning branch.

## 3. File-by-file implementation map

### Phase A — Security and data-boundary repair (first code milestone)

| File | Planned change | Required verification |
|---|---|---|
| `xparallel/workspace.py` | Define trusted authenticated actor → workspace membership resolution. Treat request workspace IDs as selectors, never proof of access. | Owner/admin/member/viewer access matrix; cross-workspace denial |
| `xparallel/authz.py` | Extend existing role/action policy only where required; avoid a second auth system. | Role/action allow-deny tests |
| `xparallel/server.py` | Apply trusted workspace authorization before reads/writes on memory, conversation, graph, Omni and task routes. Keep public routes explicitly allowlisted. | Route-by-route authorization and regression tests |
| `xparallel/audit.py` | Reconcile the allowlist with actual emitted actions; add stable event names and compatibility mapping. | Every emitted event accepted; unknown events rejected |
| `xparallel/audit_repository.py` | Ensure audit writes are consistent and failures cannot silently misreport a successful mutation. Define transaction/outbox behavior where stores differ. | Failure injection; idempotency; mutation/audit consistency |
| AROT adapter file in PR #59 | Map AROT lifecycle events to approved audit event contracts; do not send unregistered `arot:` names. | AROT create/update/verify/dispatch event tests |

**Acceptance gate:** no memory, conversation, knowledge, graph or task data may be read or modified across workspaces by changing a request parameter.

### Phase B — Memory and knowledge reconciliation

| File | Planned change | Required verification |
|---|---|---|
| `xparallel/memory_vault.py` | Retain as the existing memory persistence/deduplication service; add only compatible metadata/query interfaces needed by AILLM. | Persistence, deduplication, workspace isolation, deletion |
| `xparallel/conversation_store.py` | Keep conversation history in the existing memory database; align workspace/actor checks and retention semantics. | Save/list/delete/restart tests |
| `xparallel/omni_genome.py` | Retain Omni records, sources, versions, verifications and events; add indexed query/relationship support only after schema review. | Migration, version history, provenance, scoped search |
| `xparallel/graph.py` | Keep its existing solution-graph responsibility. Do not repurpose it as the Knowledge Genome. | Existing graph API regression tests |
| `xparallel/logarithmic_engine.py` (new) | Implement normalized logarithmic frequency/importance scoring and a transparent combined relevance score. | Numerical bounds, monotonicity, zero-input and edge-case tests |
| `xparallel/log_learning.py` (new) | Coordinate acquire → understand → encode → remember → verify → improve over existing stores. | Ingestion provenance, duplicate handling, controlled updates |
| `xparallel/log_recall.py` (new) | Rank existing memory and Omni candidates using semantic, contextual, evidence and recency signals; do not imply semantic search until a real embedding/index is configured. | Ranking benchmark against lexical baseline |
| `xparallel/log_verify.py` (new) | Represent source quality, confidence, contradictions and verification outcomes. Confidence must not be presented as truth. | Contradiction, unsupported-claim and evidence tests |
| `tests/test_ailmm.py` (new) | Cover scoring, ingest, recall, persistence and feedback. | Automated test suite |
| `tests/test_ailmm_security.py` (new) | Cover authorization, tenant isolation, provenance and deletion. | Security regression suite |

### Phase C — API and integration boundaries

| File | Planned change | Required verification |
|---|---|---|
| `xparallel/server.py` | Extend existing route groups only after inventory; avoid duplicate memory/knowledge routes. Keep backwards compatibility or version breaking changes. | OpenAPI diff and route contract tests |
| `xparallel/parallel_intelligence.py` | Keep provider invocation explicit and independently inspectable; distinguish model outputs from verified conclusions. | Mocked provider failures, timeout and partial-result tests |
| `xparallel/roaming_registry.py` | Keep agent identity/registration metadata separate from user identity and credentials. | Registration, revocation and ownership tests |
| `xparallel/roaming_worker.py` | Allowlist task types, enforce approval and emit verifiable results. | Unauthorized task rejection and replay/idempotency tests |
| `app/api/chat/route.js` | Preserve server-side credential use and authenticated XParallel routing; never expose XP_TOKEN to the browser. | Origin/auth/error handling and integration tests |
| `app/assistant/` and existing chat UI files | Connect ƎllE task/approval/evidence states after backend contracts stabilize. | Browser flow and accessible state tests |
| `app/api/` provider routes from PR #48 | Connect provider catalogue/settings only after secret-safety review; paid provider activation remains separately approved. | No-secret response tests and policy tests |

### Phase D — Workspace, website and independent products

| Area | Planned change | Required verification |
|---|---|---|
| Axaliai website files from PR #60 | Retain as umbrella public site; describe architecture separately from verified live services. | Build, route, accessibility and content accuracy |
| `oneai-workspace` repository | Keep as workspace UI candidate; replace unapproved standalone chat gateway dependency with documented server-side ƎllE/XParallel contracts. | Chat persistence, module navigation and API failure states |
| `nexai-platform` repository | Preserve separate auth, workspace, memory and product lifecycle. Add optional adapter only after explicit API contract and user consent. | Independent release tests plus adapter isolation tests |
| `ideas-platform-` repository | Recover and import the user's existing milestone implementation into its existing release branch; do not recreate from a starter. | Source inventory, dependency audit and full historical test rerun |
| UnitAI / Omnibox / Jellybox / Build Studio / AI Repair Shop / Parallel Verse | Register owner, API, data ownership, maturity and deployment for each before connecting. | Contract tests per product |

## 4. Database boundaries

Keep the current logical ownership and SQLite-first posture:

- `XP_MEMORY_DB`: Memory Vault and conversation history.
- `OMNI_DB`: Omni Genome records, sources, versions, verifications and events.
- `XP_DB_PATH`: existing solution repository and audit ledger.

Do not combine these files prematurely. Cross-database workflows are not one atomic transaction; use idempotent operations, explicit operation status and a recoverable outbox/event strategy. Verify persistent writable storage, backup and restore on the actual deployment platform before production use. A `/tmp` default is not a durable-storage guarantee.

## 5. Required environment and secret policy

- Never print or copy secret values into logs, docs, browser bundles or API responses.
- Keep `XP_TOKEN` server-side only.
- Do not enable paid providers or create paid resources without separate approval.
- Provider configuration must not be treated as proof of provider health or remaining free quota.
- Keep local/open-source provider options as the default where practical.
- Document required variable names and purpose, not their values.

## 6. Release gates

A release candidate is not ready until all gates pass:

1. Existing tests and new tests pass on the combined candidate.
2. Workspace isolation is proven across every sensitive route.
3. Audit events are compatible and mutation/audit failure behavior is explicit.
4. Chat uses the intended authenticated backend and reports errors truthfully.
5. Memory and knowledge survive process restart on durable storage.
6. Backup and restore are demonstrated.
7. Deletion/retention and concurrency behavior are tested.
8. Provider credentials remain server-side and unconfigured providers fail safely.
9. Roaming/execution tasks require allowlisting, authorization and approval.
10. Website claims match verified runtime capabilities.
11. Independent products remain independently deployable.
12. No production deployment, main merge, paid activation or DNS change occurs without explicit approval.

## 7. Execution order and status

| Order | Work package | Status |
|---:|---|---|
| 0 | Repository and PR audit | Completed as read-only assessment |
| 1 | File-level integration plan | Recorded in this document |
| 2 | Fresh PR diff reconciliation | Pending |
| 3 | Security and audit fixes | Pending |
| 4 | AILLM/Omni integration | Pending |
| 5 | ƎllE chat and workspace integration | Pending |
| 6 | IDEAS source recovery | Pending source archive/repository access |
| 7 | End-to-end verification | Pending |
| 8 | Release candidate review | Pending explicit approval |

**Current branch contains planning documentation only. No application source code has been changed by this plan.**


## 8. Fresh pull-request diff reconciliation (2026-11-10)

Fresh GitHub metadata confirms:

- PR #48 is open/draft, based on `main`, head `feat/oneai-hybrid-free-access-hub`.
- PR #49 is open/draft, based on PR #48's head, head `fix/elle-chat-error-transparency`.
- PR #59 is open/draft, based on `main`, head `feat/elle-omni-knowledge-genome`.
- PR #60 is open/draft, based on `main`, head `feat/axaliai-infrastructure-website`.
- All four PRs report mergeable at the time inspected; that flag is not a substitute for integration tests.

### Exact duplicate content between PR #48 and PR #59

The following PR patches are byte-identical in the fetched diffs, so the same changes must not be applied twice:

- `app/api/providers/route.js`
- `docs/oneai-hybrid-free-access-hub.md`
- `tests/test_free_access_hub.py`
- `tests/test_hybrid_chat.py`
- `tests/test_provider_catalog.py`
- `xparallel/free_access_hub.py`
- `xparallel/hybrid_chat.py`
- `xparallel/provider_catalog.py`

PR #59 includes a larger integration patch than PR #48 for `xparallel/server.py` and `.github/workflows/xparallel-tests.yml`; review those as combined backend/workflow changes rather than assuming either patch is a drop-in replacement.

### Critical frontend reconciliation

- `app/api/chat/route.js) is changed by all four PRs. PR #49 contains the explicit authenticated-only XParallel chat gateway and truthful failure handling. PR #60's small change is part of the website route split. Resolve this file manually against the intended `/assistant` architecture; never reintroduce public/demo chat fallbacks.
- `app/page.js) is changed by all four PRs. PR #60 replaces the root assistant interface with the Axaliai public website. Keep that website at `/`; retain the assistant UI under `/assistant`. Port Free Access Hub and provider metadata UI into the assistant page deliberately rather than restoring the assistant to the root route.
- `app/globals.css) has identical PR #48/#59 hub additions, while PR #60 adds the larger website stylesheet. Combine both sets without deleting existing assistant styles.
- `index.html) patches in PR #49 and #59 are identical; include once if that legacy page remains in the active product route/build.

### Revised integration sequence

1. Use PR #59 as the main backend integration candidate only after validating its full diff and workflow changes; it already contains the byte-identical Free Access Hub modules/tests/docs from PR #48.
2. Reconcile PR #49's authenticated chat route on top of the PR #59 candidate, because PR #49 is based on #48 and #59's route patch is not byte-identical. Validate all chat payload, timeout, error, origin and workspace assumptions.
3. Keep PR #60's public website root-page replacement. Integrate assistant and provider-hub UI at `/assistant`, not by replacing the website root.
4. Merge CSS carefully and preserve the website and assistant design systems.
5. Do not merge #48 separately if its identical provider-hub implementation has already been adopted from #59. Close/retarget PRs only after explicit review and approval; this plan does not change PR states.

**No PR was merged or modified during this diff reconciliation.**
