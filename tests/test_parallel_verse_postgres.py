"""Opt-in integration tests for Parallel Verse PostgreSQL.

Set XP_VERSE_DATABASE_URL to a disposable test database with migration 0001 applied.
Never point this test at production data.
"""
import os, unittest, uuid
from xparallel import parallel_verse_postgres as pg

@unittest.skipUnless(os.getenv("XP_VERSE_DATABASE_URL"), "requires disposable PostgreSQL database")
class ParallelVersePostgresTests(unittest.TestCase):
    def setUp(self): self.workspace="test_"+uuid.uuid4().hex
    def test_records_persist_and_are_workspace_scoped(self):
        agent=pg.register_agent(self.workspace,"Test planner",metadata={"test":True})
        space=pg.create_space(self.workspace,"Test space")
        task=pg.create_task(self.workspace,"Persist task",space_id=space["space_id"],created_by=agent["agent_id"])
        pg.record_event(self.workspace,"test.persisted",{"ok":True},space_id=space["space_id"],agent_id=agent["agent_id"])
        self.assertEqual(pg.list_agents(self.workspace)[0]["agent_id"],agent["agent_id"])
        self.assertEqual(pg.list_spaces(self.workspace)[0]["space_id"],space["space_id"])
        self.assertEqual(pg.list_tasks(self.workspace)[0]["task_id"],task["task_id"])
        self.assertIn("test.persisted",{e["event_type"] for e in pg.list_events(self.workspace)})
        self.assertEqual(pg.list_agents(self.workspace+"_other"),[])
    def test_rejects_cross_workspace_references(self):
        agent=pg.register_agent(self.workspace,"Private agent")
        with self.assertRaisesRegex(ValueError,"agent_id_not_found_in_workspace"):
            pg.create_task(self.workspace+"_other","No cross workspace",created_by=agent["agent_id"])
if __name__=="__main__": unittest.main()
