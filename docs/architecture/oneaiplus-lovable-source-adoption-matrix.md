# Oneaiplus Lovable source adoption matrix

Audit date: 2026-11-16. This document records read-only inspection of the four accessible Lovable projects. It is an adoption plan, not evidence that source code has been merged.

## Canonical destination

- Project: Oneaiplus
- Lovable project ID: `c2232890-a16d-4289-b2f8-c8de6365a7b4`
- Current commit inspected: `b3bf7af550553de782cd4e6bb9280ed57dd393ea`
- Stack: TanStack Start + TypeScript, React 19, Vite 8.
- Publication: unpublished.
- Current canonical project template marker: `.lovable/project.json` = `tanstack_start_ts_current`.
- Existing enterprise catalogue still contains 0/113 canonical component rows and 4/15 identity references. Its current `EvidenceStatus` type supports only `Not yet verified` and `Planned`; it does not yet model the authoritative evidence vocabulary.

## Source-by-source adoption

### OneAI Workspace

- Project ID: `c7f1e64a-d093-4b2c-9c09-7b8a47bbd2f6`
- Commit inspected: `9978295b23a833de87a291c3f0c234efc51134c1`
- Stack: TanStack Start + TypeScript, compatible framework family with canonical Oneaiplus.

| Source path | Observed behavior | Oneaiplus decision |
|---|---|---|
| `src/lib/workspace-schema.ts` | Zod schemas for section IDs, saved records, GitHub repo names and task inputs | Reuse/adapt validators after reconciling the canonical section slugs and existing schemas. |
| `src/components/ThemeToggle.tsx` | Accessible theme toggle with local preference | Reuse behavior only if canonical theme controls do not already cover it. Avoid duplicate theme state. |
| `src/components/WorkspaceTools.tsx` | Save/list/delete records, AI task modes, file context, GitHub repo selector and activity | Reuse UI interaction patterns selectively; canonical equivalents and permission boundaries must be checked first. |
| `src/lib/workspace.functions.ts` | Authenticated server functions, user-scoped Supabase reads/writes, audit, health and AI calls | Do not copy directly. Reconcile with canonical server functions, table ownership, identity claims, rate limits and server-only secrets. No database changes are authorized. |
| `src/components/AppShell.tsx` | Workspace navigation and responsive shell | Canonical shell already exists. Compare behavior; do not replace canonical navigation wholesale. |
| `src/components/HomeChat.tsx` and `src/routes/api/chat.ts` | AI chat and API route | Canonical chat already uses `/api/chat`; compare error handling and transport without changing provider or auth configuration. |

Security findings from source review:
- Record operations derive `user_id` from authenticated server context and constrain updates/deletes by both record ID and user ID. Preserve that property in any future adaptation.
- The Workspace task runner imports GitHub context and XParallel health server-side. Do not expose server environment values or tokens in browser code.
- This source project has its own `workspace_records` and `workspace_audit` migrations. They are not proof that the canonical project's schema is compatible.

### Pixel Perfect Replica

- Project ID: `f81f245c-8558-4b6d-bc5a-9ccaff7727d9`
- Commit inspected: `c83cda619251b8796f91077a4450693581896351`
- Stack: TanStack Start + TypeScript.

| Source path | Observed behavior | Oneaiplus decision |
|---|---|---|
| `src/lib/enterprise.ts` | Role helpers, product status labels, React Query data loaders for users/products/audit | Reuse role vocabulary only as a design reference; canonical owner-only authorization model takes precedence until an explicit multi-role policy is approved. |
| `src/routes/_authenticated/admin.users.tsx` | Admin user and role management UI | Do not import or activate. It writes role rows and introduces admin/operator/member semantics not established in canonical Oneaiplus. |
| `src/test/permissions.test.ts` | Tests for admin/operator/member permission matrix | Keep as reference test patterns only; do not apply a new role model by implication. |
| `src/test/app-routing.test.tsx` | Route smoke test without loaders/network | Reuse the testing approach where applicable. |

The donor schema/migrations include profiles, role assignments, products, audit events, helper functions and triggers. Do not copy these migrations, RLS policies, auth triggers, role tables or client-side mutations into canonical Oneaiplus without a separately approved, isolated security design.

### Pixel Perfect Replay

- Project ID: `91552ebf-59d2-4c69-b5be-d9e0ff926909`
- Commit inspected: `3e99bffcafe71abc213728600341af3b4362ee18`
- Publication: published. No edits, unpublish actions or visibility changes were made.

This project substantially overlaps the responsive navigation/shell patterns already present in Oneaiplus and OneAI Workspace. Preserve it as an independent source project; use it for comparison and visual reference only. Do not copy a second shell or alter its published state.

## Canonical implementation state verified

- Oneaiplus already contains Command Center, Ecosystem, Identities, Verification Center, Workspace, Builder, XParallel, Parallel Intelligence, AI Mixer, Omni Engine, Jellybox, UnitAI, Omnibox, AI Repair Shop, UIDaaS, Integrations, Deployments and Settings routes/panels.
- `src/lib/enterprise-inventory.ts` currently has an empty `registeredComponents` array and only four non-authoritative identity references.
- `src/components/modules/enterprise.tsx` currently labels the catalogue as static/source inventory and explicitly reports 0/113; Verification Center still says the authoritative register is not supplied.
- `src/lib/sections.ts` defines the existing navigation sections. Keep these route slugs stable when mapping source components to workspace pages.
- `src/lib/module-status.ts` has execution disabled; do not infer execution readiness from UI presence.

## Safe next implementation sequence

1. Import the structured registry at `docs/architecture/oneaiplus-ecosystem-registry.json` into the canonical TanStack project, retaining C001–C113 and P001–P015 source IDs and original status labels.
2. Update canonical inventory types to support all six source statuses: Unverified, Existing and verified, Partial, Planned, Experimental and Blocked.
3. Add source category, responsibility, proposed owner, dependencies, acceptance evidence and status to catalogue detail views.
4. Reconcile the 15 identities separately; do not silently count Oneaiplus, NexAI or IDEAS as replacement identities. Preserve the source identity list and independence boundary.
5. Map each component to an existing section only where the mapping is justified; do not create 113 routes or claim all components are operational.
6. Add catalogue tests for exact IDs/counts/statuses, filters, detail rendering, independent product boundaries and empty/error handling.
7. Verify preview routes and mobile layouts; separately verify server-side behavior only where permitted.
8. Leave database, auth/RLS, secrets, integrations, publishing and production deployment untouched unless separately approved.

## Current blockers

- The canonical Lovable project exposes read-only project files through the available connection; a writable, zero-cost source path to this exact TanStack project has not been established.
- The GitHub repository used for the staging branch contains a Next.js 14 frontend and is not proven to be the synchronized source of the canonical TanStack Lovable project.
- The staged JSON and Node test file are in the isolated GitHub branch. The JSON has been parsed and structurally validated; the Node test has not yet been executed in CI.
- Therefore, this branch is not yet a canonical Lovable preview update. Do not report the catalogue as imported into the preview until the actual project commit and preview are verified.
