# Oneaiplus Source Consolidation Audit

Audit date: 2026-11-14
Canonical Lovable project: Oneaiplus (`c2232890-a16d-4289-b2f8-c8de6365a7b4`)
Workspace: `ff79e3a0f86ba2c60f87`
Backend/source repository: `axali-sys/Unity-AI-Voice-Interface`

## Canonical project decision

Oneaiplus is the sole user-facing enterprise workspace. The three other Lovable projects remain read-only donors until their reusable work is selectively ported:
- OneAI Workspace (`c7f1e64a-d093-4b2c-9c09-7b8a47bbd2f6`): earlier home/chat, workspace table, theme toggle, workspace records and chat server.
- Pixel Perfect Replica (`f81f245c-8558-4b6d-bc5a-9ccaff7727d9`): authenticated dashboard/admin patterns, role/permission tests and enterprise layout.
- Pixel Perfect Replay (`91552ebf-59d2-4c69-b5be-d9e0ff926909`): earlier navigation shell and route structure.

Do not delete, rename, publish, or overwrite donor projects as part of consolidation.

## Verified Oneaiplus source structure

The Oneaiplus Lovable source is accessible through the Lovable project file API. It is a TanStack Start + React + TypeScript application, with Drizzle migration files, Supabase auth integration, server functions, module panels, and owner-only middleware. Its current project commit is `3fac96efc001f394622301568f2f42417c08a87a`.

Key files:
- `src/components/AppShell.tsx`, `src/lib/sections.ts`: navigation and module map.
- `src/components/modules/panels.tsx`, `ModulePage.tsx`, `shared.tsx`: module implementations.
- `src/lib/diagnostics.functions.ts`: server-side read-only probes, memory CRUD, audit listing.
- `src/lib/owner.functions.ts`, `src/lib/owner-access.ts`, `src/integrations/supabase/auth-middleware.ts`: owner authorization.
- `drizzle/migrations/0000..0002_*.sql`: owner access, projects, memories and audit events.
- `src/components/HomeChat.tsx`, `src/server/chat.server.ts`: AI chat path.

## Consolidation map

| Donor | Reusable capability | Destination |
|---|---|---|
| OneAI Workspace | Workspace records/table and theme toggle | Oneaiplus Workspace + Settings |
| OneAI Workspace | Chat UI/server patterns | Oneaiplus HomeChat; retain current owner checks and explicit provider errors |
| Pixel Perfect Replica | Admin dashboard and permission-test patterns | UIDaaS/Security, after policy review |
| Pixel Perfect Replay | Route and navigation patterns | AppShell/sections only where they improve current navigation |
| All donors | Shared shadcn/Radix UI primitives | Reuse only when versions and dependencies match; avoid duplicate primitive copies |

## Verified blockers and safety findings

1. Oneaiplus module panels currently identify file attachments/saved research threads as not built.
2. Omni and UnitAI plans are stored in browser `sessionStorage`, not account persistence.
3. Parallel Intelligence / Mixer currently present model selection UI but route all model calls through the Lovable AI Gateway; no independent provider adapters are connected.
4. XParallel integration currently performs only read-only GET probes to `/public/health`, `/public/xparallel/access`, and `/public/system`. The UI records the last known `403 origin_not_allowed`. Private `/chat` and `/execute` are not wired.
5. Execution is intentionally denied because the server-enforced approval and governance proof are not complete.
6. Jellybox memory and audit operations exist in server functions and migration SQL, but live owner-session, deployed schema and RLS behavior still require runtime verification. The checked-in `drizzle/schema.ts` is an auto-generated blank stub, so migration SQL—not that stub—is the current evidence for those tables.
7. The source explicitly records an AI Gateway `402 Not enough credits` blocker. No paid request or credit purchase is authorized.
8. Builder, deployment actions and provider integrations must not claim operational status without live verification.

## Safe implementation sequence

1. Export/attach the Oneaiplus source to a source-controlled branch without changing production.
2. Add regression tests for owner access, memory isolation, audit immutability, disabled execution and provider-unavailable states.
3. Port the OneAI Workspace records/theme capabilities into Oneaiplus, adapting schemas and routes rather than copying a second app shell.
4. Port the Pixel Perfect Replica admin/permission patterns only after reconciling its roles with Oneaiplus owner-only access.
5. Persist Omni/UnitAI drafts in owner-scoped database tables.
6. Add provider-neutral adapter interfaces and local deterministic tests; do not imply live model inference without a configured provider.
7. Add XParallel server-to-server adapter only after host auth/origin contract is verified; keep `XP_TOKEN` server-only and execution disabled.
8. Run build, lint, unit, auth/RLS and preview smoke tests before proposing any release.

## Release constraints

- No production deployment or publishing.
- No merge to `main`.
- No purchases or paid services.
- Keep NexAI and IDEAS independent.
- Preserve all source projects and histories.
- Distinguish implemented, tested, blocked and research-only capabilities.
