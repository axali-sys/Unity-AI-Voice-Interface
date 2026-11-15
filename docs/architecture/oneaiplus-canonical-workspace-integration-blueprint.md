# Oneaiplus Canonical Workspace Integration Blueprint

**Date:** 2026-11-16  
**Canonical Lovable project:** `c2232890-a16d-4289-b2f8-c8de6365a7b4`  
**Inspected canonical source SHA:** `b3bf7af550553de782cd4e6bb9280ed57dd393ea`  
**Purpose:** implementation blueprint for bringing selected OneAI Workspace features into the actual Oneaiplus TanStack Start source.

## Canonical source facts observed

- App shell: `src/components/AppShell.tsx`; route navigation is generated from `src/lib/sections.ts`.
- Existing core workspace section slug: `workspace`.
- Existing Builder section slug: `builder`.
- Existing Projects dashboard is already linked in the shell.
- Authentication: `src/lib/owner.functions.ts` uses `requireSupabaseAuth` and `is_oneai_owner` RPC; `requireOwnerAccess` fails closed.
- Existing chat: `src/components/HomeChat.tsx`, POST `/api/chat`.
- Existing status gates: `src/lib/module-status.ts`; execution and deployment actions are disabled.
- Existing roadmap records AI chat blocked on AI credits (HTTP 402).
- The canonical project is unpublished. Its preview is not evidence of live model execution.

## Integration map

| OneAI Workspace donor feature | Oneaiplus canonical destination | Integration approach |
|---|---|---|
| WorkspaceTools UI | Existing `workspace` section / ModulePage | Extend the existing workspace page; do not add a duplicate top-level workspace |
| Task modes | Existing chat/task server boundary | Define validated task input schema and server-side dispatch; enable only modes with verified backend support |
| Workspace records | Dedicated owner-scoped server functions | Persistence is blocked until the actual database target, schema and RLS isolation are verified |
| GitHub repository context | Existing Builder and `github.functions.ts` | Reuse the canonical server connector where possible; start read-only; never send credentials to the client |
| File context | Existing chat/workspace UI | Enforce size/type limits; treat file text as untrusted; no default persistent storage |
| Activity history | Existing audit/verification patterns | Show only persisted, source-backed events; no synthetic run history |
| XParallel health | Existing XParallel module | Read-only HTTPS health check; never imply authorization or execution from health alone |

## Mandatory security review discovered

The current `src/lib/projects.functions.ts` is protected by `requireOwner`, but its handlers:
- list projects without an explicit `.eq("user_id", context.userId)` filter;
- update by `id` without an explicit owner predicate;
- delete by `id` without an explicit owner predicate.

This may be additionally constrained by database RLS, but that cannot be assumed from the source alone. Before reusing this pattern or adding saved workspace records:
1. Inspect the actual database schema and RLS policies read-only.
2. Verify whether the authenticated principal is a single owner or whether workspace-level isolation is intended.
3. Ensure update/delete predicates include the verified owner key as defense in depth.
4. Add cross-owner negative tests.
5. Do not change migrations, RLS, auth triggers, database configuration or production data under this task.

## Safe implementation order

1. Add the workspace tools interface to the existing `workspace` module without creating new data persistence.
2. Implement client-side draft state and truthful status labels for task modes.
3. Integrate read-only GitHub context through existing canonical server-side connector functions, after confirming the exact function contracts and permissions.
4. Add server-side task mode validation; keep unsupported modes disabled.
5. Review and harden owner-scoped project/record operations only after RLS/database evidence is available.
6. Add tests for validation, owner isolation, secret non-disclosure, error handling and fail-closed execution.
7. Verify the canonical Lovable preview and record the exact commit and test evidence.

## Hard boundaries

- No Lovable editor-credit spend is authorized by this blueprint.
- No AI Gateway, paid model, paid integration, subscription or other purchase.
- No database writes, DDL, migrations, seeds, RLS/auth changes or secrets changes.
- No publishing, production deployment, merge to main/default branch, or production modifications.
- No changes to the donor OneAI Workspace project; its identity and history remain intact.
- NexAI and IDEAS remain independent.
- Do not claim implementation until code is present in the verified canonical source and the canonical preview has been tested.

## Source binding blocker

The accessible canonical Lovable project is TanStack Start / React 19. The GitHub repository previously named by the user, `axali-sys/Unity-AI-Voice-Interface`, has a Next.js frontend at repository root and is not positively identified as the canonical Oneaiplus source. No source write may target that repository as if it were the canonical frontend until the exact Lovable GitHub repository and branch binding is evidenced.
