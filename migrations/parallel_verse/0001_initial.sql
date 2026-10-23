-- XParallel Parallel Verse PostgreSQL schema (migration 0001)
-- Apply only to a dedicated development/test database first.
CREATE TABLE IF NOT EXISTS verse_agents (
  agent_id text PRIMARY KEY, workspace_id text NOT NULL, name text NOT NULL,
  kind text NOT NULL, status text NOT NULL, metadata_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_verse_agents_workspace ON verse_agents(workspace_id, created_at DESC);
CREATE TABLE IF NOT EXISTS verse_spaces (
  space_id text PRIMARY KEY, workspace_id text NOT NULL, name text NOT NULL,
  description text NOT NULL DEFAULT '', created_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_verse_spaces_workspace ON verse_spaces(workspace_id, created_at DESC);
CREATE TABLE IF NOT EXISTS verse_events (
  event_id text PRIMARY KEY, workspace_id text NOT NULL, space_id text, agent_id text,
  event_type text NOT NULL, payload_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_verse_events_workspace ON verse_events(workspace_id, created_at DESC);
CREATE TABLE IF NOT EXISTS verse_tasks (
  task_id text PRIMARY KEY, workspace_id text NOT NULL, space_id text, created_by text,
  assigned_to text, title text NOT NULL, description text NOT NULL DEFAULT '',
  status text NOT NULL, result_json jsonb, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_verse_tasks_workspace ON verse_tasks(workspace_id, created_at DESC);
