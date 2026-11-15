# Oneaiplus Persistent Workspace and Chat Migration Proposal

Date: 2026-11-15
Status: Proposal only — NOT applied

## Purpose

Define a safe, reversible first database milestone for Oneaiplus: persistent section-scoped workspace records and persistent conversations/messages. This proposal does not authorize a production migration. It is intended for review and isolated-database testing only.

## Preconditions

- Confirm the exact canonical Lovable source-control remote and development branch.
- Reconstruct the complete canonical database state from migrations 0000–0002 and compare it with the live database before drafting executable SQL.
- Confirm the installed Supabase/PostgreSQL version and available extensions.
- Create an isolated database or branch with no production data.
- Back up and verify restore before any non-disposable database test.
- Keep the existing owner-only authorization model. Do not import donor role tables or donor RLS policies.

## Proposed schema

### workspace_records

Fields:
- `id uuid primary key default gen_random_uuid()`
- `user_id uuid not null`
- `section text not null`
- `record_type text not null default 'note'`
- `name text not null`
- `content text not null default ''`
- `status text not null default 'saved'`
- `metadata jsonb not null default '{}'`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`

Constraints:
- Bound section, record_type and status to explicit allowlists in application validation and preferably database CHECK constraints.
- Require non-empty names and impose practical maximum lengths on name/content.
- Require metadata to be a JSON object and impose a bounded serialized size in server validation.
- Index `(user_id, section, updated_at DESC)`.
- RLS SELECT/INSERT/UPDATE/DELETE policies must require both `user_id = auth.uid()` and `public.is_oneai_owner()`.
- Server functions must derive user_id from validated auth context, never accept it as a client authority.

### conversations

Fields:
- `id uuid primary key default gen_random_uuid()`
- `user_id uuid not null`
- `title text not null default 'New conversation'`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`
- `archived_at timestamptz null`

Constraints and indexes:
- Non-empty title with a conservative maximum length.
- Index `(user_id, updated_at DESC)`.
- RLS for all operations requires both owner identity checks.
- Only expose conversations belonging to the authenticated owner.

### conversation_messages

Fields:
- `id uuid primary key default gen_random_uuid()`
- `conversation_id uuid not null references public.conversations(id) on delete cascade`
- `user_id uuid not null`
- `role text not null`
- `content text not null`
- `sequence integer not null`
- `created_at timestamptz not null default now()`
- `metadata jsonb not null default '{}'`

Constraints and indexes:
- Role allowlist: user, assistant, system, tool. Tool/system persistence should be disabled until the application explicitly needs it and defines safe handling.
- Unique `(conversation_id, sequence)`.
- Index `(conversation_id, sequence)`.
- Enforce child ownership by checking that the parent conversation has the same user_id and belongs to the current authenticated owner. A simple child-row `user_id` check alone is insufficient.
- Use database policies with an EXISTS check against the parent conversation for SELECT/INSERT/UPDATE/DELETE. Also validate parent ownership in server functions.
- Do not store API keys, bearer tokens, passwords, connector secrets, or raw credential payloads in content or metadata.
- Set explicit message-size limits and validate JSON metadata size in server functions.

## Audit strategy

Use the existing `public.audit_events` table rather than introducing a second audit table.

Before implementation:
- Decide whether the current `action text` and `detail text` fields are sufficient or whether a separately reviewed migration should add structured `metadata jsonb`.
- Add server-side audit writes for workspace record create/update/delete and conversation create/archive/delete.
- Do not log full message bodies or sensitive connector content.
- Preserve the current lack of authenticated UPDATE/DELETE policies.
- Decide transaction semantics: ideally write the mutation and its audit event atomically in a database function/RPC. Do not silently swallow audit-write failures for security-sensitive mutations.

## Migration order

1. Add tables, constraints, indexes and RLS policies.
2. Add narrowly scoped server functions for list/create/update/delete of workspace records.
3. Add conversation create/list/rename/archive/delete and message append/list functions.
4. Add atomic audit functions or transactionally coupled server operations.
5. Add UI only after server and RLS tests pass.
6. Leave current `projects` and `memories` tables intact; no data migration or destructive consolidation in this first release.

## Required security tests

Run against an isolated Supabase/Postgres environment with at least:
- unauthenticated request;
- authenticated user who is not the configured Oneaiplus owner;
- configured owner;
- forged user_id in request body;
- owner attempting to read another user's record ID;
- owner attempting to read another user's conversation ID;
- child message insert where message user_id differs from parent owner;
- child message read when parent conversation is not owned;
- malformed UUIDs, invalid roles, oversized content and oversized metadata;
- deletion of a conversation and confirmation that child messages cascade;
- audit event creation on each supported mutation;
- attempt to update/delete audit rows as authenticated user;
- service-role credentials never present in browser bundles or client responses.

Expected result: all unauthorized and cross-owner cases are denied by database policy, not merely hidden in UI.

## Rollback and recovery

- Take a verified backup before applying to any persistent environment.
- Keep the migration additive: no dropping or renaming existing tables/columns.
- Roll back by disabling new UI/routes first, then dropping only newly introduced tables/functions/indexes in reverse dependency order on the isolated test database.
- Never run destructive rollback against a database containing user-created records without an explicit export and recovery decision.
- Preserve existing `projects`, `memories`, and `audit_events`.

## Acceptance criteria

- Existing login, owner checks, projects and memories continue working.
- RLS tests prove owner-only access and cross-record isolation.
- Conversation messages persist and reload in stable sequence.
- Conversation deletion removes its messages.
- Audit entries are appended for supported mutations and cannot be edited/deleted by authenticated clients.
- No credentials are stored in browser code or chat records.
- Migration and rollback have both been exercised in an isolated environment.
- No production deployment or publication change is part of this milestone.

## Explicit non-actions

This is a written proposal, not executable SQL and not an applied migration. No database writes, source-code edits, donor migrations, merge to main, production deployment, or paid service use occurred.
