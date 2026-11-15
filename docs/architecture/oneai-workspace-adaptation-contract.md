# OneAI Workspace → Oneaiplus Adaptation Contract

**Status:** isolated implementation specification; not a canonical UI integration  
**Source:** `axali-sys/oneai-workspace` main, audited 2026-11-16  
**Destination:** Oneaiplus Lovable project `c2232890-a16d-4289-b2f8-c8de6365a7b4`  
**Rule:** preserve both project identities and histories; no publish, deployment, merge to default branch, paid activation, or database mutation.

## 1. Integration intent

Oneaiplus remains the canonical workspace. OneAI Workspace is a donor of selected capabilities, not an application to replace or wholesale merge. Implement donor capabilities using Oneaiplus's existing TanStack Start/React 19 shell, route structure, owner identity model, server boundary, and visual language.

## 2. Audited donor capabilities and decisions

| Donor source | Capability | Decision | Required adaptation |
|---|---|---|---|
| `src/components/WorkspaceTools.tsx` | Workspace records, task modes, file context, GitHub repository selection and activity | Adapt selectively | Retain useful interaction patterns; reconcile all modes and IDs with Oneaiplus navigation and canonical task contracts |
| `src/lib/workspace-schema.ts` | Zod validation for records, section IDs, repositories and task inputs | Reuse concepts, not blindly copy | Map section IDs to `src/lib/sections.ts`; validate server-side; reject unknown modes and oversized inputs |
| `src/lib/workspace.functions.ts` | Authenticated server functions and owner-scoped operations | Port only after security review | Derive owner from verified Oneaiplus session; never accept caller-supplied owner IDs; constrain every read/update/delete by owner |
| `src/server/connectors.server.ts` | Server-side GitHub repository listing and read-only repository context | Adapt behind server-only adapter | Never expose connector credentials; allowlist repository paths/actions; initially read-only; redact secrets and bound response size |
| `src/server/workspace-ai.server.ts` | AI task modes and model calls | Do not transplant provider implementation | Donor requires Lovable AI Gateway credentials and model availability; Oneaiplus must use its own provider-neutral gateway and truthful availability/errors |
| `src/server/xparallel.server.ts` | HTTPS health check | Reuse concept | Health-only, strict HTTPS, timeout, validated response; never infer private execution permission from reachability |
| `src/components/ThemeToggle.tsx` | Theme preference toggle | Compare before reuse | Keep canonical theme implementation if equivalent; avoid duplicate state or conflicting local-storage keys |
| Donor Supabase persistence | Workspace records and audit | Do not copy schema/migrations | No DDL, migrations, seeds, triggers, auth or RLS changes without separate approval and verified database isolation |

## 3. Canonical integration sequence

1. **Workspace interface:** add a Oneaiplus-native workspace tools surface using existing shell and route conventions.
2. **Task contract:** expose only task modes with a verified Oneaiplus server implementation; show unavailable modes as unavailable, not as working.
3. **Record persistence:** begin read-only or disabled until the canonical database target and owner isolation are proven. If no safe persistence path exists, keep session-only drafts and label them accurately.
4. **GitHub context:** add a server-only read adapter, initially limited to repository metadata and explicitly selected files. No commits, PR writes, branch mutation or secret access from the workspace UI without separate approval.
5. **File context:** validate file type and size, handle content as untrusted input, and do not persist uploaded content by default.
6. **Activity:** display only events returned by an authoritative source; do not fabricate task history.
7. **XParallel health:** show reachability and version separately from authorization, approvals, execution and receipt verification.

## 4. Mandatory security invariants

- Resolve the user from Oneaiplus's verified server session.
- Enforce owner scoping server-side for every record operation.
- Keep all provider, GitHub and XParallel credentials server-side.
- Validate every input with schemas at the server boundary.
- Apply bounded timeouts, payload limits and safe error messages.
- Treat imported repository text, files, memory and model outputs as untrusted data.
- Fail closed when identity, authorization, approval, revocation or provider state is missing.
- Never represent a UI route, health endpoint, test stub or CI pass as proof of live AI execution.
- Preserve Oneaiplus's existing owner-only authorization model; do not import donor role systems.

## 5. Acceptance tests required before enabling each feature

- Unauthenticated requests are rejected.
- A user cannot read, update or delete another owner's records by changing IDs or payload fields.
- Unknown task modes, section IDs and repository identifiers are rejected.
- Credentials are absent from browser bundles, client responses and logs.
- GitHub adapter rejects unapproved write operations and path traversal.
- File uploads enforce type/size limits and are not persisted without explicit consent.
- AI provider failure, missing credentials, rate limits and empty outputs are surfaced honestly.
- XParallel health failure and timeout remain non-authorizing; private execution remains separately approval-gated.
- Audit/activity entries correspond to actual persisted events.
- Existing Oneaiplus navigation, chat route, owner session and execution/deployment gates remain intact.

## 6. Current blockers

- The exact GitHub repository/branch synchronized to the canonical Oneaiplus Lovable project is not yet verified. The known Unity-AI-Voice-Interface repository frontend is Next.js 14, while the canonical Lovable project is TanStack Start.
- The Oneaiplus draft uses a `local_supabase` backend label, which does not prove isolated database ownership. No database writes or migrations are permitted until isolation is verified.
- Donor AI code depends on Lovable AI Gateway credentials and paid/limited provider availability; it is not a zero-cost fallback.
- A canonical Oneaiplus preview update has not been made by this specification.

## 7. Completion definition

This contract is complete only when each selected feature is implemented in the verified canonical Oneaiplus source, passes the acceptance tests, appears in the canonical preview, and carries evidence-backed status. Until then, it remains an implementation specification and the donor project remains intact.
