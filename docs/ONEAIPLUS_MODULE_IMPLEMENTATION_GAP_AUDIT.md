# Oneaiplus Module Implementation Gap Audit

Date: 2026-11-14
Audited source: Oneaiplus Lovable project `c2232890-a16d-4289-b2f8-c8de6365a7b4`, current HEAD at inspection.
Method: source-file inspection only; no source writes, database writes, builds, or deployments.

## Executive result

The application has a usable owner-authenticated shell and several real server-backed capabilities, but most enterprise modules are still interface prototypes or diagnostics. The current UI is transparent about many blockers; this audit records the concrete implementation gaps so subsequent work can be tested rather than judged by labels.

## Module-by-module findings

| Module | Current implementation evidenced in source | Gap / next work |
|---|---|---|
| AI Workspace | Home chat exists; UI reports AI Gateway 402 | Provider-independent gateway, attachment handling, saved conversation threads, tests without paid credits |
| Builder | Builder panel links to repository tooling | Verify GitHub server functions, repository/branch permissions, diff review and PR workflow; no autonomous merge |
| XParallel | Three read-only public GET probes; private `/chat` and `/execute` are blocked | Fix server-to-server origin policy; define signed service identity and server-side auth; keep execution denied until governance tests pass |
| Parallel Intelligence | Model checkbox and prompt UI | Actual adapters, provider credentials held server-side, parallel calls, timeout/cost controls, synthesis and evidence records |
| AI Mixer | Same UI/runtime as Parallel Intelligence | Separate orchestration policies and provider adapters; no provider fan-out is operational today |
| Omni Engine | Draft plan steps stored in browser `sessionStorage` | Owner-scoped persistent plans, schema validation, versioning, audit and run history |
| UnitAI | Same browser-only planner component as Omni | Reusable unit/agent registry, capability manifests, least-privilege grants, persistent workflows and run logs |
| Jellybox | Server functions read/write memories and audit events | End-to-end session/RLS testing, retrieval ranking, retention/export controls and operational tests |
| Omnibox | Currently renders the Integrations panel | Dedicated service registry, permissions, connector health and approved action catalogue |
| Integrations | GitHub/database/XParallel probes; Vercel and Render shown unconnected | Workspace-level connector setup; account-level Render/Vercel intentionally postponed |
| AI Repair Shop | Runs read-only GitHub/database/XParallel diagnostics and prints suggestions | Evidence-backed issue records, repair plans and isolated test execution; no automatic repair today |
| UIDaaS | Displays current session and owner check; one owner role | Maintain single-owner model until a real role/invitation threat model and tests exist |
| Settings & Security | Environment presence booleans and audit list | Secret rotation workflow, session controls, audit export, permission policy review |
| Deployment Center | Displays preview and blocked release actions | Build/test evidence and release approvals; production deploy/merge remain disabled |

## Concrete code-level observations

1. `PlannerPanel` stores Omni and UnitAI plans in `sessionStorage`, keyed by `oneai-omni-plan` / `oneai-unit-plan`. Data is browser-tab/device scoped and not persisted to the owner account.
2. `ModulePage` routes both `omnibox` and `integrations` to `IntegrationsPanel`; Omnibox therefore has no independent service catalogue.
3. `MultiModelPanel` renders model identifiers but all calls are described as going through Lovable AI Gateway. The UI disables execution because the gateway returned HTTP 402. The displayed model list is not proof that those providers are connected.
4. `probeXParallel` only sends GET requests to `/public/health`, `/public/xparallel/access`, and `/public/system`. It does not call `/chat`, `/execute`, or any mutating endpoint.
5. `executionGate` always returns `allowed: false`; the reason explicitly cites missing server-enforced approval and unresolved XParallel governance issues.
6. `getEnvStatus` returns Vercel and Render as hardcoded false; no connector is wired in this project.
7. `RepairShopPanel` is diagnostic-only. It does not edit repositories, run CI, or deploy.
8. `projects.functions.ts` and diagnostics/memory functions use owner middleware and derive `user_id` from authenticated server context. These patterns should be reused, not bypassed.
9. The live migrations define `projects`, `memories`, and `audit_events`; the current Drizzle schema file is a blank stub. Do not run Drizzle schema pushes until the schema is reconstructed and compared against live SQL.
10. `saveProject` has no explicit audit write in the inspected function; add auditable create/update/delete events before treating project management as fully accountable.
11. The `projects.repo` column is globally UNIQUE in the migration. If the application later supports multiple workspaces/owners, revisit this constraint before adding multi-tenant repository records.
12. Audit table policies permit authenticated SELECT and INSERT only, which is consistent with append-only client behavior. Server-side service-role access remains privileged and must not be exposed to the browser.

## Recommended implementation order

### Gate 0 — establish a source-controlled, isolated Oneaiplus development copy
- Export or connect the canonical Lovable project source to GitHub using Lovable's supported project integration.
- Keep the existing source repository `axali-sys/Unity-AI-Voice-Interface` intact; it contains the XParallel backend and is not a substitute for the Oneaiplus TanStack Start frontend.
- Create a separate development branch/repository for Oneaiplus source changes. No merge to main and no production publish.

### Gate 1 — restore baseline build and test evidence
- Reproduce the existing reported TypeScript/build issue in `panels.tsx`.
- Run formatter, lint, typecheck, unit tests and production build in the isolated copy.
- Add tests for owner middleware, status classification, execution denial, and planner input validation.
- Capture baseline before changing behavior.

### Gate 2 — persistent Omni and UnitAI
- Implement the `workflow_plans` and `workflow_runs` schema from the persistence design document.
- Reconstruct Drizzle schema from verified migrations before using Drizzle migrations.
- Add owner RLS, same-owner plan/run relationship enforcement, bounded Zod validation, audit events and indexes.
- Replace browser-only sessionStorage planners with server functions and account-scoped query state.
- Keep run mode simulation/read-only by default; execution remains denied.

### Gate 3 — real connector registry and Omnibox
- Separate Omnibox route from Integrations.
- Store connector metadata and permission grants, never provider secrets in client state.
- Show configured, connected, authorized and tested as distinct states.

### Gate 4 — XParallel integration
- Repair public endpoint origin handling without weakening authentication.
- Add a private chat path separate from execution; normal chat must not be affected by execution revocation checks.
- Keep execution disabled until approval, revocation, identity binding, idempotency, audit, rate limits and cross-tenant tests pass.

### Gate 5 — model adapters and Parallel Intelligence
- Use open-source/local provider options first where feasible.
- Implement server-side provider adapter contracts and health checks.
- No paid model service or credit purchase without explicit approval.

## Acceptance criteria

A module is not marked Operational merely because its panel renders. It must have:
- an implemented server path,
- authentication/authorization checks,
- meaningful input validation,
- tests that pass,
- a successful real end-to-end check,
- auditable state changes where relevant,
- truthful UI status and a documented dependency list.

## Safety / scope constraints

- $0 only; no paid subscriptions, credits, purchases or usage commitments.
- No production deployment, publishing, or merge to main.
- Keep Render/Vercel account-level connection work paused.
- Keep NexAI and IDEAS independent.
- Preserve donor Lovable projects and their histories.
- Never claim DRI consciousness or real intelligence beyond demonstrated behavior.
- Do not apply XParallel execution revocation to normal conversational chat.
