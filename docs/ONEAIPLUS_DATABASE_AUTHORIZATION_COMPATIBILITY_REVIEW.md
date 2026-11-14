# Oneaiplus Database and Authorization Compatibility Review

Date: 2026-11-15

## Scope
Read-only comparison of canonical Oneaiplus migrations, OneAI Workspace donor migration and workspace server functions, and Pixel Perfect Replica migration. No SQL was applied and no project source was modified.

## Canonical Oneaiplus security baseline
The canonical migration `0000_oneai_owner_access.sql` defines `public.is_oneai_owner()` as SECURITY DEFINER with an empty search_path and restricts execution to authenticated/service_role. It checks the authenticated UID against the configured owner email and confirmed-email status. The auth trigger rejects other account emails.

The canonical `projects` and `memories` RLS policies require both `user_id = auth.uid()` and `public.is_oneai_owner()`. This is a stronger boundary than row ownership alone.

The canonical `audit_events` table grants authenticated SELECT/INSERT, with owner-scoped RLS. There are no authenticated UPDATE/DELETE policies in the reviewed migration. The table is therefore a natural audit foundation, subject to server-side write design and service-role handling.

## OneAI Workspace donor compatibility
The donor migration creates `workspace_records` and `workspace_audit`.

Findings:
- `workspace_records` RLS checks only `auth.uid() = user_id`; it does not invoke `is_oneai_owner()`.
- `workspace_audit` likewise checks only row ownership.
- The `record_workspace_audit()` trigger is SECURITY DEFINER with `search_path = public`, unlike the canonical hardened empty search_path pattern.
- The donor audit table has a trigger-generated history, but it is a separate table with a different event shape and authorization policy.
- Donor server functions do filter by `context.userId` and use authenticated middleware. This is useful application-level scoping but does not repair the weaker database policy.
- The donor `runWorkspaceAI` can read Jellybox section records as contextual memory and can add GitHub repository context. These are useful workflows but should be reimplemented against canonical authorization and provider constraints.

Decision: do not copy the donor migration or enable its tables in the canonical database unchanged. Map the useful record model to a canonical schema with owner enforcement at both server and RLS layers. Reuse canonical `audit_events` where its event structure is sufficient, or propose a compatible extension only after migration review.

## Pixel Perfect Replica role-system compatibility
The donor migration defines `app_role`, `profiles`, `user_roles`, `has_role()`, and product/audit tables.

Findings and risks:
- The signup trigger grants admin to the first user based on whether any admin role currently exists. This bootstrap rule needs concurrency-safe and operationally controlled provisioning before multi-user production use.
- The SECURITY DEFINER `has_role()` function uses `search_path = public`; it should be hardened and have explicit execution grants/revokes.
- The role policies permit admin role insertion when `has_role(auth.uid(),'admin')` is true. Any adoption requires a careful proof against recursive-policy issues and privilege escalation paths.
- The role revocation policy prevents an admin from deleting their own role but does not constitute a complete, tested governance lifecycle.
- The donor's product and audit tables have a different data model and should not be imported as-is.
- UI-level roles or hidden controls are not authorization; every privileged operation needs server-side checks and restrictive RLS.

Decision: retain Oneaiplus's existing owner-only model for the current single-owner phase. Do not import the donor role system until a separate multi-tenant/workspace security architecture, controlled role provisioning, hardened functions, and adversarial RLS tests exist.

## Recommended canonical data model

### Workspace records
Add a canonical `workspace_records` table only after deciding whether `projects` and `memories` remain dedicated domain tables or are represented by a generic record layer. Avoid silently duplicating those concepts.

Suggested fields: `id`, `user_id`, `section`, `record_type`, `name`, `content`, `status`, `metadata`, `created_at`, `updated_at`. Enforce owner identity in server middleware and RLS. Validate section/type/status values and bound text/JSON sizes. Index `(user_id, section, updated_at DESC)`.

### Chat history
Use separate `conversations` and `conversation_messages` tables. Each row should carry `user_id`; message rows should also reference the parent conversation. Enforce parent/child ownership in database policies, not only client filters. Validate role values, message length, ordering, and content types. Define deletion behavior so deleting a conversation removes its messages. Keep provider credentials and raw secrets out of messages and metadata. Establish retention/export/deletion semantics before enabling persistence.

### Audit
Prefer canonical `audit_events` with structured event metadata over a second donor audit table. Writes should occur server-side after authorization. Authenticated users should not gain UPDATE/DELETE rights. Avoid logging tokens, message bodies, credentials, or sensitive connector payloads. Define whether audit failure blocks the associated mutation or is handled through a durable transactional mechanism.

## Implementation gates
1. Reconstruct canonical schema from authoritative SQL migrations; do not rely on the currently blank generated Drizzle schema.
2. Write migrations with explicit rollback notes and test on an isolated database/draft.
3. Add RLS tests for owner, unauthenticated user, authenticated non-owner, cross-user child rows, and service-role-only operations.
4. Add server-function tests for missing auth, denied owner, malformed payloads, cross-record IDs, and audit behavior.
5. Only then implement persistence UI and enable writes.

## Non-actions
- No migration applied.
- No database writes or policy changes.
- No donor source or schema copied.
- No role provisioning, project merge, deployment, or publication change.
- Render and Vercel connections remain deferred.
