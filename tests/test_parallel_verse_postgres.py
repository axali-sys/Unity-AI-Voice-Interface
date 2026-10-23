"""Opt-in PostgreSQL integration tests for Parallel Verse.

Use only a disposable PostgreSQL database with migrations 0001 and 0002 applied.
Never point these tests at production data. The CI suite runs this module with no
database URL to verify importability; database integration tests are then skipped.
"""
import os
import unittest
import uuid
from datetime import datetime, timezone

from xparallel import parallel_verse_postgres as pg

@unittest.skipUnless(os.getenv("XP_VERSE_DATABASE_URL"), "requires disposable PostgreSQL database")
class ParallelVersePostgresTests(unittest.TestCase):
    def setUp(self):
        self.workspace = "test_" + uuid.uuid4().hex

    def test_records_persist_and_are_workspace_scoped(self):
        agent = pg.register_agent(self.workspace, "Test planner", metadata={"test": True})
        space = pg.create_space(self.workspace, "Test space")
        task = pg.create_task(self.workspace, "Persist task", space_id=space["space_id"],
                              created_by=agent["agent_id"])
        pg.record_event(self.workspace, "test.persisted", {"ok": True},
                        space_id=space["space_id"], agent_id=agent["agent_id"])
        self.assertEqual(pg.list_agents(self.workspace)[0]["agent_id"], agent["agent_id"])
        self.assertEqual(pg.list_spaces(self.workspace)[0]["space_id"], space["space_id"])
        self.assertEqual(pg.list_tasks(self.workspace)[0]["task_id"], task["task_id"])
        self.assertIn("test.persisted", {e["event_type"] for e in pg.list_events(self.workspace)})
        self.assertEqual(pg.list_agents(self.workspace + "_other"), [])

    def test_rejects_cross_workspace_references_in_adapter(self):
        agent = pg.register_agent(self.workspace, "Private agent")
        with self.assertRaisesRegex(ValueError, "agent_id_not_found_in_workspace"):
            pg.create_task(self.workspace + "_other", "No cross workspace",
                           created_by=agent["agent_id"])

    def test_database_rejects_cross_workspace_references(self):
        import psycopg
        agent = pg.register_agent(self.workspace, "Constraint test")
        now = datetime.now(timezone.utc)
        with self.assertRaises(psycopg.errors.ForeignKeyViolation):
            with pg._connect() as conn, conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO verse_tasks
                    (task_id, workspace_id, space_id, created_by, assigned_to, title,
                     description, status, result_json, created_at, updated_at)
                    VALUES (%s,%s,NULL,%s,NULL,%s,'','open',NULL,%s,%s)""",
                    ("tsk_" + uuid.uuid4().hex, self.workspace + "_other",
                     agent["agent_id"], "cross-workspace must fail", now, now),
                )

if __name__ == "__main__":
    unittest.main()
