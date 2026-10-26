import tempfile
import unittest
from pathlib import Path

from xparallel.parallel_verse import (
    create_space,
    create_task,
    discover_agents,
    list_agents,
    list_events,
    list_spaces,
    list_tasks,
    record_event,
    register_agent,
)


class ParallelVerseTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp_dir.name) / "verse.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_agent_and_event_survive_reopening_database(self):
        agent = register_agent("alpha", "Planner", metadata={"role": "planning"}, db_path=self.db)
        # A fresh call opens the database again, simulating a new request/process.
        agents = list_agents("alpha", db_path=self.db)
        self.assertEqual(agents[0]["agent_id"], agent["agent_id"])
        self.assertEqual(agents[0]["metadata"]["role"], "planning")
        self.assertTrue(any(event["event_type"] == "agent.registered"
                            for event in list_events("alpha", db_path=self.db)))

    def test_workspaces_are_isolated(self):
        register_agent("alpha", "Alpha agent", db_path=self.db)
        self.assertEqual(list_agents("beta", db_path=self.db), [])
        self.assertEqual(list_events("beta", db_path=self.db), [])

    def test_space_task_and_event_history(self):
        agent = register_agent("alpha", "Worker", db_path=self.db)
        space = create_space("alpha", "Research", "Shared research area", db_path=self.db)
        task = create_task("alpha", "Compare providers", space_id=space["space_id"],
                           created_by=agent["agent_id"], assigned_to=agent["agent_id"],
                           db_path=self.db)
        record_event("alpha", "agent.message", {"text": "Starting research"},
                     space_id=space["space_id"], agent_id=agent["agent_id"], db_path=self.db)
        self.assertEqual(list_spaces("alpha", db_path=self.db)[0]["space_id"], space["space_id"])
        self.assertEqual(list_tasks("alpha", db_path=self.db)[0]["task_id"], task["task_id"])
        types = {event["event_type"] for event in list_events("alpha", db_path=self.db)}
        self.assertTrue({"agent.registered", "space.created", "task.created", "agent.message"} <= types)

    
    def test_discovers_agents_by_declared_capability(self):
        planner = register_agent(
            "alpha", "Research Planner", kind="planning",
            metadata={"capabilities": ["research", "summarization"]},
            db_path=self.db,
        )
        register_agent(
            "alpha", "Code Worker", kind="coding",
            metadata={"capabilities": ["testing", "repair"]},
            db_path=self.db,
        )
        register_agent(
            "beta", "Private Researcher", kind="research",
            metadata={"capabilities": ["research"]},
            db_path=self.db,
        )
        matches = discover_agents("alpha", capability="RESEARCH", db_path=self.db)
        self.assertEqual([item["agent_id"] for item in matches], [planner["agent_id"]])
        self.assertEqual(discover_agents("alpha", capability="repair", db_path=self.db)[0]["name"],
                         "Code Worker")
        self.assertEqual(discover_agents("alpha", capability="unknown", db_path=self.db), [])

    def test_rejects_cross_workspace_references(self):
        agent = register_agent("alpha", "Private agent", db_path=self.db)
        with self.assertRaisesRegex(ValueError, "agent_id_not_found_in_workspace"):
            create_task("beta", "Steal assignment", created_by=agent["agent_id"], db_path=self.db)

    def test_rejects_invalid_inputs(self):
        with self.assertRaises(ValueError):
            register_agent("alpha", " ")
        with self.assertRaises(ValueError):
            create_space("alpha", "")
        with self.assertRaises(ValueError):
            record_event("alpha", "", {})


if __name__ == "__main__":
    unittest.main()
