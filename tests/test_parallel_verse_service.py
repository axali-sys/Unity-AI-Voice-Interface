import tempfile, unittest
from pathlib import Path
from xparallel.parallel_verse_service import ParallelVerseService

class ParallelVerseServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.db=str(Path(self.temp.name)/"verse.sqlite3")
        self.sessions={"alpha":{"authenticated":True,"workspace_id":"ws-a","subject":"user-a"},
                       "beta":{"authenticated":True,"workspace_id":"ws-b","subject":"user-b"}}
        self.allowed=True
        self.service=ParallelVerseService(authenticate=lambda s:self.sessions.get(s,{"authenticated":False}),
          authorize=lambda p,a,r:self.allowed and a in {"agent.create","agent.read","space.create","space.read","event.write","event.read","task.create","task.read"},
          db_path=self.db)
    def tearDown(self): self.temp.cleanup()
    def test_workspace_comes_from_trusted_session_not_client_argument(self):
        agent=self.service.register_agent("alpha",name="Planner",metadata={"capabilities":["research"]})
        self.assertEqual(agent["workspace_id"],"ws-a")
        self.assertEqual(self.service.list_agents("beta"),[])
        with self.assertRaises(TypeError):
            self.service.list_agents("alpha",workspace_id="ws-b")
    def test_spaces_events_and_tasks_are_scoped_and_persisted(self):
        agent=self.service.register_agent("alpha",name="Worker")
        space=self.service.create_space("alpha",name="Research")
        task=self.service.create_task("alpha",title="Review sources",space_id=space["space_id"],
          created_by=agent["agent_id"],assigned_to=agent["agent_id"])
        self.service.record_event("alpha",event_type="agent.message",payload={"text":"hello"},
          space_id=space["space_id"],agent_id=agent["agent_id"])
        self.assertEqual(self.service.list_tasks("alpha")[0]["task_id"],task["task_id"])
        self.assertGreaterEqual(len(self.service.list_events("alpha")),4)
        self.assertEqual(self.service.list_tasks("beta"),[])
    def test_auth_and_acl_fail_closed(self):
        with self.assertRaises(PermissionError): self.service.list_agents("invalid")
        self.allowed=False
        with self.assertRaises(PermissionError): self.service.register_agent("alpha",name="No")
    def test_secret_metadata_rejected(self):
        with self.assertRaises(ValueError):
            self.service.register_agent("alpha",name="Bad",metadata={"api_token":"do-not-store"})
    def test_cross_workspace_references_rejected(self):
        agent=self.service.register_agent("alpha",name="Private")
        with self.assertRaises(ValueError):
            self.service.create_task("beta",title="Cross tenant",created_by=agent["agent_id"])
if __name__=="__main__": unittest.main()
