# XParallel Parallel Verse API (development)

These authenticated endpoints expose the first persistent world primitives:

- `POST /verse/agents` — register an agent. JSON: `{"name":"Planner","kind":"planning","metadata":{"purpose":"research"},"workspace_id":"default"}`
- `GET /verse/agents?workspace_id=default` — list agents in a workspace.
- `POST /verse/spaces` — create a space. JSON: `{"name":"Research","description":"Shared research area","workspace_id":"default"}`
- `GET /verse/spaces?workspace_id=default` — list spaces.
- `POST /verse/events` — append an event. JSON: `{"event_type":"agent.message","payload":{"text":"Hello"},"agent_id":"agt_...","space_id":"spc_...","workspace_id":"default"}`
- `GET /verse/events?workspace_id=default` — list recent events.
- `POST /verse/tasks` — create a task. JSON: `{"title":"Compare providers","description":"Assess configured providers","space_id":"spc_...","created_by":"agt_...","assigned_to":"agt_...","workspace_id":"default"}`
- `GET /verse/tasks?workspace_id=default` — list tasks.

All routes require the existing bearer-token authentication. Writes additionally pass the existing `create_solution` role check; reads pass the existing `read` role check. Records are workspace-scoped. Agent registration, space creation, and task creation append events to the event history. The first version does not execute agent code or autonomously modify agent prompts/models.

## Persistence caveat

The SQLite adapter uses `XP_VERSE_DB`. By default, local runs use `.xparallel/parallel_verse.db`; serverless runs use `/tmp/.xparallel/parallel_verse.db` only as a fallback. **Vercel /tmp is ephemeral and is not durable production storage.** Before relying on persistence across deployments or cold starts, configure `XP_VERSE_DB` to a durable mounted volume or replace the SQLite adapter with managed PostgreSQL and migrations. The API does not currently prove that the configured path is durable, so deployment readiness must remain unverified until that infrastructure is configured and tested.

## Security and tenancy boundary

The current server uses the existing shared bearer-token authorization model. The caller supplies `workspace_id`; the API does not yet derive workspace membership from a verified per-user identity. Therefore, workspace filters prevent accidental mixing in storage operations, but **they are not sufficient isolation for untrusted multi-tenant clients sharing the same token**. Keep these routes behind trusted server-side access until identity-to-workspace authorization is implemented and tested. Never ship `XP_TOKEN` to the browser.

## Current boundaries

- The API supports registration, spaces, append-only event history, and task records.
- Tasks are records only; no scheduler or autonomous multi-agent execution is implemented yet.
- Memory retention, event archival, concurrency/load testing, and migrations are future work.
- Treat metadata and event payloads as untrusted user data. Never put secrets in them.
