# Oneaiplus Live Database Verification

Verification date: 2026-11-14
Project: Oneaiplus (`c2232890-a16d-4289-b2f8-c8de6365a7b4`)
Method: read-only catalog queries through the project's connected database.

## Confirmed live state

The project's Supabase database is enabled.

Public tables present:
- `projects`
- `memories`
- `audit_events`

Row-level security is enabled on all three tables.

Policies observed:
- `projects`: authenticated users require `user_id = auth.uid()` and `is_oneai_owner()` for all operations.
- `memories`: authenticated users require the same owner check for all operations.
- `audit_events`: authenticated users may select and insert only rows where `user_id = auth.uid()` and `is_oneai_owner()`. No authenticated update/delete policy was observed.

The deployed `public.is_oneai_owner()` function is SQL, STABLE, SECURITY DEFINER, and sets an empty search_path. It checks that the current authenticated user exists in `auth.users`, matches the configured owner email, and has a confirmed email. Execute is revoked from PUBLIC and anon, and granted to authenticated and service_role.

The deployed account restriction trigger rejects auth user inserts/updates unless the email matches the configured owner email.

## Important qualifications

- This verifies database objects and policy definitions, not a successful end-to-end login or a negative cross-user access test.
- RLS is enabled but `FORCE ROW LEVEL SECURITY` is false on these tables. Table owners and privileged service roles can bypass ordinary RLS; service-role credentials must remain server-side and tightly controlled.
- The only observed indexes are primary-key indexes and the unique projects repo index. There are no indexes on `user_id` or `created_at` in these tables.
- The current Drizzle `schema.ts` in the Lovable source is a blank generated stub. Do not assume Drizzle schema introspection is synchronized with deployed migrations.

## Safe next improvements (proposal only; not applied)

1. Add composite indexes for owner-scoped ordered reads:
   - `projects(user_id, created_at DESC)`
   - `memories(user_id, created_at DESC)`
   - `audit_events(user_id, created_at DESC)`
2. Consider a GIN index on `memories(tags)` only if tag containment queries are implemented and query plans justify it.
3. Reconstruct and verify the Drizzle schema from the three checked-in migrations before using Drizzle migrations again.
4. Add authenticated integration tests proving owner access works and non-owner access returns no rows / cannot write.
5. Verify audit immutability at the SQL grant and RLS levels, and ensure all application audit writes are performed by trusted server functions.

No SQL writes, schema changes, data changes, credential reads, or deployments were performed during this verification.
