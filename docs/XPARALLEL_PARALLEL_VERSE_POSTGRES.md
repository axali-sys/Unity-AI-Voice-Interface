# XParallel Parallel Verse PostgreSQL readiness

## Current state and hard limits
- Development-only preparation on branch `xparallel-parallel-verse-verify`; existing PR #44 remains unmerged.
- SQLite remains the default for both Parallel Verse and chat conversations. Parallel Verse PostgreSQL is opt-in with `XP_VERSE_BACKEND=postgres`; PostgreSQL conversation history is separately opt-in with `XP_CONVERSATION_BACKEND=postgres`.
- Conversation history uses migration `0003_conversations.sql`; applying it is required before enabling the PostgreSQL conversation backend. It is not automatically applied at startup.
- No Supabase project/database is currently connected to this workspace. No paid resource has been created.
- Authorized database budget is **$0/month**. Supabase Pro is the preferred future target but must not be provisioned until a budget is explicitly approved.
- A green CI run without a database URL proves import/static and non-database tests only; PostgreSQL integration tests are skipped unless a disposable test URL is supplied.

## Migration order
1. Apply `migrations/parallel_verse/0001_initial.sql`.
2. Apply `migrations/parallel_verse/0002_workspace_integrity.sql`.
3. Apply `migrations/parallel_verse/0003_conversations.sql` only if preparing PostgreSQL-backed chat history.
4. Verify all five named foreign-key constraints exist and are validated; confirm the unique indexes `uq_verse_agents_workspace_agent` and `uq_verse_spaces_workspace_space` exist.
5. Run `python -m unittest discover -s tests -p 'test_parallel_verse_postgres.py' -v` and `python -m unittest discover -s tests -p 'test_conversation_store_postgres.py' -v` against a disposable database. Do not run against production.

Migration 0002 adds composite workspace-aware foreign keys so events/tasks cannot reference a space or agent from another workspace even if application-level checks are bypassed. It does not grant application roles access or configure RLS.

## Configuration
- Install dependencies from `requirements.txt` (includes psycopg 3 binary package).
- Set `XP_VERSE_BACKEND=postgres` to opt in to Parallel Verse PostgreSQL, and/or `XP_CONVERSATION_BACKEND=postgres` to opt in to PostgreSQL chat history. Keep both unset or set to `sqlite` to retain SQLite defaults.
- Set `XP_VERSE_DATABASE_URL` as a **server-side secret** only. Both adapters use this URL.
- Use a dedicated least-privilege application database role, not a Supabase service-role secret or a superuser for normal runtime.
- Require TLS/SSL for remote connections. Prefer Supavisor transaction pooling for serverless request workloads when compatible with the driver/workload; use a direct or session connection for migrations.
- Keep the database URL out of browser code, logs, error payloads, screenshots, and committed environment files.
- Apply migrations as a separate controlled step; application startup must not auto-migrate.

## Readiness checklist (all required before production)
- [ ] Provision a database within an explicitly approved budget; current budget prevents this.
- [ ] Apply migrations 0001 and 0002 to a disposable PostgreSQL instance and record migration versions.
- [ ] If enabling PostgreSQL chat history, apply migration 0003 and verify save/retrieve/update/delete plus workspace isolation.
- [ ] Run PostgreSQL integration tests; confirm persistence across separate connections and process restart.
- [ ] Test empty/malformed configuration, SSL connection, connection timeout, unavailable DB, and recovery behavior.
- [ ] Run the complete repository test suite and CI against the exact candidate commit.
- [ ] Run Supabase security and performance advisors after schema deployment; resolve critical findings.
- [ ] Define and test backup/restore procedure, RPO/RTO, retention, and data-export procedure.
- [ ] Add monitoring for connection saturation, latency, database size, failed queries, and storage/compute usage alerts.
- [ ] Verify request identity maps to an authorized workspace on the server. Caller-supplied workspace IDs plus a shared bearer token are not sufficient tenant isolation for public multi-tenant access.
- [ ] Review database grants/RLS before exposing tables through Supabase Data API. This app currently uses a server-side PostgreSQL adapter; do not grant anon/authenticated table access unless an independently reviewed RLS policy design is implemented.
- [ ] Test migration rollback/forward-repair on a disposable database and document recovery steps.
- [ ] Keep production on the existing backend until migration, security, operational, and deployment gates pass with explicit authorization.

## Tests
Without `XP_VERSE_DATABASE_URL`, PostgreSQL integration tests are intentionally skipped. CI should still import the adapter and run the test module so syntax/import regressions are caught. A skipped database test is **not** evidence of database readiness.
