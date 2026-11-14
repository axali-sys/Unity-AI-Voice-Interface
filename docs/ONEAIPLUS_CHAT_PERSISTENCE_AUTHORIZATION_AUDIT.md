# Oneaiplus Chat, Workspace Persistence, and Authorization Compatibility Audit

Date: 2026-11-15  
Scope: read-only inspection of the canonical Oneaiplus Lovable project and two donor projects. No application code, database schema, records, authentication settings, deployment, or publication were changed.

## Executive decision

Port the useful workspace-record and activity concepts from OneAI Workspace into Oneaiplus, but do not copy its database migration. Keep the canonical `projects`, `memories`, and `audit_events` tables as the initial persistence foundation, with a deliberate schema extension only after a migration plan and ownership rules are reviewed. Keep canonical `/api/chat` as the sole normal-chat entry point. Do not import the Pixel Perfect Replica role system into the current owner-only security model.

## 1. Canonical chat path verified

The canonical UI component `src/components/HomeChat.tsx` uses AI SDK `useChat` with `DefaultChatTransport({ api: "/api/chat" })`. It attaches the signed-in Supabase access token as a bearer token. The UI explicitly says chat is not saved and clears when the page is left.

The route `src/routes/api/chat.ts` maps POST `/api/chat` to `handleChat(request)`.

The canonical server handler `src/server/chat.server.ts`:
- Requires a bearer token and validates it with Supabase `auth.getUser`.
- Checks the canonical `is_oneai_owner` RPC before continuing.
- Uses the server-side `LOVABLE_API_KEY` and Lovable AI Gateway model `openai/gpt-6-astra`.
- Streams AI SDK UI messages and maps 402/429/auth/provider errors to user-readable messages.
- Does not persist chat messages or conversation history.

**Integration rule:** all normal Oneaiplus chat must continue through this authenticated `/api/chat` route. XParallel's private `/chat` is a separate server-to-server integration and must never be replaced by the public `/public/ask` health/discovery surface. A provider error or insufficient-credit response is a real unavailable state, not an invitation to simulate an answer.

## 2. OneAI Workspace donor persistence reviewed

Donor migration `drizzle/migrations/0000_workspace_records.sql` creates:
- `workspace_records`: user_id, section, name, content, status, metadata, created_at, updated_at.
- `workspace_audit`: user_id, action, record_name, created_at.
- A trigger that records insert/update/delete events in `workspace_audit`.

Donor server functions enforce authenticated user scoping in queries and mutations. The donor's table RLS policy checks `auth.uid() = user_id`; audit is readable by the owning user. Its audit trigger is SECURITY DEFINER with `search_path = public`.

The donor schema is useful as a feature reference, but copying its migration would create parallel record and audit systems. The canonical database already has:
- `projects` with owner-scoped records and progress/status fields.
- `memories` with owner-scoped title/body/tags.
- `audit_events` with owner-scoped append/read controls.

**Recommended mapping:**
- Project plans and milestones -> canonical `projects` where fields fit.
- Durable notes/recall -> canonical `memories`.
- Activity -> canonical `audit_events`, appended only by trusted server/database functions.
- Section-specific rich workspace artefacts -> consider a single canonical `workspace_records` extension only if the existing tables cannot represent them cleanly. Require section allowlisting, size limits, owner-scoped CRUD, timestamps, and explicit RLS tests.
- Do not create donor `workspace_audit` alongside canonical `audit_events`.

The canonical `projects.repo` unique constraint is global rather than per-user. Review this before allowing multi-workspace or multi-user reuse; do not silently alter it during feature porting.

## 3. Authorization boundaries

Canonical Oneaiplus is currently owner-only, with `requireOwner` server middleware and an `is_oneai_owner` database check. The live database audit previously verified RLS on the canonical tables and owner checks. The donor's broader authenticated-user record policy is not interchangeable with this stricter model.

The Pixel Perfect Replica donor migration creates `app_role` values admin/operator/member, `user_roles`, a SECURITY DEFINER `has_role` helper, signup role assignment, role-management policies, and product/audit tables. Its UI role controls and helper tests are not sufficient proof of safe multi-user authorization.

**Decision:** preserve canonical owner-only access. Do not copy donor role tables, first-user-admin signup behavior, or role grants into Oneaiplus. A multi-user/workspace authorization design must first define tenant boundaries, bootstrap ownership, privilege-escalation protections, function execute grants, RLS behavior, audit integrity, and recovery from accidental admin loss. The donor's `has_role` function and signup trigger need an independent security review before any reuse.

## 4. Chat history and streaming feature plan

A future chat-history implementation should:
1. Keep `/api/chat` and its bearer-token + owner validation.
2. Add a conversation/message persistence model only after choosing whether chat history belongs in the canonical database or an explicitly user-controlled local-only mode.
3. Derive owner identity from the validated server session, never from a client-supplied user_id.
4. Enforce ownership on every read, append, rename, and delete.
5. Avoid persisting hidden reasoning or provider-internal encrypted reasoning payloads.
6. Apply message size/count limits, retention controls, and clear deletion semantics.
7. Keep provider errors visible and honest; don't fabricate model output when credits or credentials are unavailable.

The donor streaming implementation is substantially the same Lovable AI Gateway pattern as the canonical implementation. It adds no reason to replace the canonical route or gateway configuration.

## 5. Next implementation sequence

1. Confirm Oneaiplus GitHub source-control linkage to the correct repository and branch before attempting application-code edits.
2. Write and review a canonical data mapping/migration plan, including the global `projects.repo` uniqueness issue.
3. Implement the section-scoped workspace record UX against canonical persistence, only if schema fit and owner authorization are verified.
4. Add server-side append-only activity events and tests.
5. Add chat history as a separate, explicitly approved persistence milestone.
6. Revisit roles only after multi-tenant security architecture is designed and tested.
7. Keep Render/Vercel account connections postponed until the user resumes that work.

## Verification and non-actions

- Inspected canonical `HomeChat.tsx`, `src/routes/api/chat.ts`, `src/server/chat.server.ts`, and `projects.functions.ts`.
- Inspected donor `workspace-schema.ts`, `workspace.functions.ts`, `drizzle/migrations/0000_workspace_records.sql`, and donor `chat.server.ts`.
- Inspected Pixel Perfect Replica `drizzle/migrations/0000_migration.sql` and `src/test/permissions.test.ts`.
- No application source files were edited.
- No database writes or migrations were executed.
- No donor project was modified or merged.
- No branch was merged, no production deployment was made, and no paid service was purchased.
