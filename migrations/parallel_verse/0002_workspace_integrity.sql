-- Parallel Verse integrity constraints.
-- Apply after 0001_initial.sql on a disposable development/test database first.
-- Composite foreign keys prevent cross-workspace references even if application checks are bypassed.

CREATE UNIQUE INDEX IF NOT EXISTS uq_verse_agents_workspace_agent
  ON verse_agents(workspace_id, agent_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_verse_spaces_workspace_space
  ON verse_spaces(workspace_id, space_id);

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_verse_events_workspace_space') THEN
    ALTER TABLE verse_events ADD CONSTRAINT fk_verse_events_workspace_space
      FOREIGN KEY (workspace_id, space_id)
      REFERENCES verse_spaces(workspace_id, space_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_verse_events_workspace_agent') THEN
    ALTER TABLE verse_events ADD CONSTRAINT fk_verse_events_workspace_agent
      FOREIGN KEY (workspace_id, agent_id)
      REFERENCES verse_agents(workspace_id, agent_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_verse_tasks_workspace_space') THEN
    ALTER TABLE verse_tasks ADD CONSTRAINT fk_verse_tasks_workspace_space
      FOREIGN KEY (workspace_id, space_id)
      REFERENCES verse_spaces(workspace_id, space_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_verse_tasks_workspace_creator') THEN
    ALTER TABLE verse_tasks ADD CONSTRAINT fk_verse_tasks_workspace_creator
      FOREIGN KEY (workspace_id, created_by)
      REFERENCES verse_agents(workspace_id, agent_id);
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_verse_tasks_workspace_assignee') THEN
    ALTER TABLE verse_tasks ADD CONSTRAINT fk_verse_tasks_workspace_assignee
      FOREIGN KEY (workspace_id, assigned_to)
      REFERENCES verse_agents(workspace_id, agent_id);
  END IF;
END $$;
