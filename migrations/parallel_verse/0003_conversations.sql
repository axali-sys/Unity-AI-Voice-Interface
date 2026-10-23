-- PostgreSQL conversation history, separate from Parallel Verse core tables.
-- Apply only to a dedicated development/test database first.
CREATE TABLE IF NOT EXISTS axaliai_conversations (
  conversation_id text NOT NULL,
  workspace_id text NOT NULL,
  title text NOT NULL DEFAULT 'New chat',
  messages_json jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at double precision NOT NULL,
  updated_at double precision NOT NULL,
  PRIMARY KEY (workspace_id, conversation_id)
);
CREATE INDEX IF NOT EXISTS idx_axaliai_conversations_workspace
  ON axaliai_conversations(workspace_id, updated_at DESC);
