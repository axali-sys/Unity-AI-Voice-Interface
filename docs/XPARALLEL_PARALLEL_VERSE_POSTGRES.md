# Parallel Verse managed PostgreSQL preparation

## Status
This is development-branch preparation only. No database/project is created by this code.
The adapter is opt-in and the existing SQLite backend remains the default.

## Configuration
- Install dependencies from requirements.txt (includes psycopg 3 binary package).
- Set `XP_VERSE_BACKEND=postgres`.
- Set `XP_VERSE_DATABASE_URL` as a server-side secret using a Supabase PostgreSQL connection string.
- Apply `migrations/parallel_verse/0001_initial.sql` to a dedicated development/test database before enabling the backend.
- For serverless workloads use Supabase's pooled transaction connection string when appropriate; consult https://supabase.com/docs/guides/database/connecting-to-postgres/pooling-and-limits.
- Never expose the connection string in browser code, logs, or API responses.

## Test
Set `XP_VERSE_DATABASE_URL` to a disposable database with migration 0001 applied, then run:
`python -m unittest tests.test_parallel_verse_postgres -v`
Without the variable, PostgreSQL integration tests are skipped. SQLite tests remain independent.

## Rollout guardrails
1. Keep production on SQLite/current configuration until an approved managed database exists.
2. Verify schema migration, CRUD, workspace filtering, restart persistence and connection behavior in a disposable database.
3. Do not switch production merely by setting an environment variable.
4. Workspace IDs are still caller-supplied under the current shared bearer-token model. Add verified identity-to-workspace authorization before exposing to untrusted multi-tenant clients.
5. Free-tier use can be paused due to inactivity and has a 500 MB database limit. Supabase Pro has a fixed subscription charge plus compute/usage charges; the user's current authorized database budget is $0, so Pro provisioning is blocked pending explicit budget approval.
