# Oneaiplus Lovable Project Consolidation Map

**Status:** isolated engineering record; no production changes  
**Canonical destination:** Lovable project `c2232890-a16d-4289-b2f8-c8de6365a7b4` (Oneaiplus)  
**Audit date:** 2026-11-16  
**Scope:** consolidate useful capabilities from the owner's Lovable workspace into Oneaiplus without deleting, renaming, or overwriting source projects.

## 1. Governing decisions

- Oneaiplus is the sole canonical workspace and integration destination.
- Preserve the source projects, their histories, and their independent identities.
- NexAI and IDEAS remain independent products and are not absorbed into Oneaiplus.
- Do not publish, deploy, merge to the default branch, or make production changes.
- Do not spend credits or activate paid services.
- Do not copy database migrations, auth policies, secrets, or privileged configuration between projects.
- A visible screen, route, component name, or roadmap entry is not proof that its underlying capability works.
- Keep XParallel's private execution and authorization boundary separate from public UI and browser code.

## 2. Audited Lovable workspace sources

| Project | Project ID | Observed foundation/state | Reuse decision |
|---|---|---|---|
| Oneaiplus | `c2232890-a16d-4289-b2f8-c8de6365a7b4` | TanStack Start + TypeScript; canonical enterprise navigation, chat, owner sign-in, module routes and inventory pages; unpublished at audit | Keep as destination and preserve its current shell, routes, chat and security model |
| OneAI Workspace | `c7f1e64a-d093-4b2c-9c09-7b8a47bbd2f6` | TanStack Start; workspace records, search, theme control, task modes, GitHub read-only connector surface | Adapt UI patterns and validated workflows; do not copy its Supabase tables/server functions without a schema and owner-isolation review |
| Pixel Perfect Replica | `f81f245c-8558-4b6d-bc5a-9ccaff7727d9` | TanStack Start; enterprise dashboard, people, products/catalogue and audit concepts; separate role model | Reuse presentation and domain concepts only; do not transplant `admin/operator/member` roles, RLS, triggers or migrations into Oneaiplus |
| Pixel Perfect Replay | `91552ebf-59d2-4c69-b5be-d9e0ff926909` | TanStack Start; alternate navigation/responsive patterns; published at audit | Read-only reference. Preserve its publication state; borrow only demonstrably useful UI patterns |

## 3. Canonical Oneaiplus baseline

The inspected Oneaiplus source establishes:
- `src/lib/sections.ts` as the current navigation/module registry.
- `src/components/AppShell.tsx` as the responsive shell and owner sign-out surface.
- `src/components/HomeChat.tsx` as the existing AI chat client using the canonical `/api/chat` route.
- `src/components/modules/enterprise.tsx` and `src/lib/enterprise-inventory.ts` as the current enterprise inventory and evidence presentation.
- The enterprise inventory currently contains **0/113 authoritative component entries** and four documented identity references; these are explicitly not represented as a complete register.
- Execution and deployment actions are gated in the existing module-status policy.

The canonical Lovable project identifies its template as `tanstack_start_ts_current`. The connected GitHub repository's inspected frontend branch uses Next.js 14. Do not replace the canonical frontend with that Next.js application or assume the repository's current frontend is a synchronized export of this Lovable project.

## 4. Authoritative ecosystem register

Use the existing register as the source of truth:
- `docs/architecture/113-component-register.md`
- 10 categories, exactly 113 component entries.
- 15 preservation identities are tracked separately and excluded from the 113 count.
- Statuses must remain evidence-based: Unverified, Existing and verified, Partial, Planned, Experimental, or Blocked.
- Do not manufacture missing component IDs or promote a component to verified based on its name or UI presence.

The 15 preservation identities must remain discoverable and traceable. The independently operated NexAI and IDEAS products are outside that 15-identity consolidation scope unless the owner explicitly changes the boundary.

## 5. Integration mapping

### OneAI Workspace → Oneaiplus
Candidate adaptations:
- searchable workspace navigation and useful theme-toggle behavior;
- named records and task-history interaction patterns;
- selected research/compare/plan/repair workflows where the canonical server-side model gateway supports them;
- GitHub repository browsing as a read-only, least-privilege capability initially.

Required adaptation:
- use Oneaiplus's existing verified identity/session context;
- scope every record and query to the authenticated owner on the server;
- validate inputs and section identifiers at the server boundary;
- keep credentials server-side;
- preserve `/api/chat` as the canonical chat route;
- prove persistence isolation before enabling writes.

### Pixel Perfect Replica → Oneaiplus
Candidate adaptations:
- catalogue/product inventory views;
- people and organization directory presentation;
- audit-event exploration;
- operational dashboard layout and status vocabulary.

Required adaptation:
- map these concepts onto the existing Oneaiplus owner-only access model;
- no implicit creation of team roles or user administration;
- audit views must read authoritative events, not locally fabricated activity;
- no database schema or policy copying without separate explicit authorization and target-isolation evidence.

### Pixel Perfect Replay → Oneaiplus
Candidate adaptations:
- responsive navigation details and layout refinements only after comparison against the canonical shell.

Do not copy a second application shell or duplicate routes merely to make the projects look merged.

### Unity-AI-Voice-Interface repository → Oneaiplus
Repository: `axali-sys/Unity-AI-Voice-Interface`  
Existing source branch: `oneaiplus/unification-foundation-2026-11-14`

Candidate donor scope:
- XParallel backend and interoperability services;
- execution authorization, leases, revocation, receipts and worker lifecycle code;
- architecture documentation and test evidence.

Compatibility boundary:
- repository frontend is Next.js 14, whereas the canonical Lovable Oneaiplus frontend is TanStack Start;
- use backend contracts and independently portable modules, not wholesale frontend replacement;
- verify the actual host identity resolver, active grants, approvals, runtime revocation and signed receipt lifecycle before enabling private execution;
- do not expose XP_TOKEN, host credentials, or privileged API keys to the browser;
- public health/status endpoints are not authorization for private execution.

## 6. Proposed implementation order

1. **Register import:** expose all 113 source register entries and 15 identity records in Oneaiplus using source-backed IDs and status values. Preserve category counts and links to evidence.
2. **Enterprise read surfaces:** adapt catalogue, audit and people-directory concepts as read-only views against verified sources.
3. **Workspace UX:** adapt search, theme and record-management UI; keep persistence disabled until canonical server-side owner scoping and isolation are verified.
4. **XParallel backend integration:** connect through server-side adapters with explicit timeouts, allowlists, authentication and fail-closed authorization.
5. **Model gateway and collaborative intelligence:** separate provider-neutral gateway, user-facing AI Mixer, and Parallel Intelligence synthesis; report provider availability and errors honestly.
6. **Verification:** run typecheck, build, unit/integration tests, responsive checks and security review. Attach evidence per component; leave unverified entries unverified.
7. **Release gate:** no publish, production deployment, merge to default branch, database migration, or paid activation without the owner's separate approval.

## 7. Acceptance criteria

- Oneaiplus remains the only canonical workspace and existing route/chat behavior is preserved.
- All four Lovable projects remain intact; Pixel Perfect Replay publication state is unchanged.
- The 113-component count and 15-identity count are source-backed and separately reported.
- Every imported item has a stable source ID, owner, responsibility, dependency/overlap notes, and evidence status.
- No donor database/auth/security configuration is transplanted.
- Every persistence operation is server-authorized and owner-scoped.
- XParallel private execution fails closed unless trusted identity, ownership, capability, explicit approval, expiry, resource limits and runtime revocation are checked.
- All changes remain on isolated `oneaiplus/*` development branches until reviewed.

## 8. Current limitations and honest status

This document records a source audit and an integration contract. It does not claim that source files have already been copied into the canonical Lovable project, that the Lovable preview has changed, or that any provider, database, XParallel host, or private execution path is operational.

The Lovable source files were readable through the connected project integration. The GitHub repository is accessible, but its inspected Next.js frontend has not been proven to be the canonical Lovable project's synchronized source. Therefore this branch is an isolated engineering record, not proof of a completed Lovable-to-GitHub source binding.
