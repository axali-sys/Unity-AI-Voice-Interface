"""Safety and contract tests for the opt-in AxaliAI Roaming orchestration."""
import unittest
from unittest.mock import patch

from xparallel import roaming_ai


class RoamingValidationTests(unittest.TestCase):
    def test_rejects_empty_objective(self):
        with self.assertRaisesRegex(ValueError, "query_required"):
            roaming_ai.run_roaming_task("   ")

    def test_rejects_oversized_objective(self):
        with self.assertRaisesRegex(ValueError, "query_too_large"):
            roaming_ai.run_roaming_task("x" * (roaming_ai.MAX_OBJECTIVE_CHARS + 1))


class RoamingExecutionTests(unittest.TestCase):
    @patch("xparallel.roaming_ai.search_memories", return_value=[
        {"id": "m1", "summary": "test memory", "content": "untrusted reference"}
    ])
    @patch("xparallel.roaming_ai.route", return_value={"mode": "local", "resources": [{"id": "r1"}]})
    @patch("xparallel.roaming_ai.chat_with_ai")
    def test_three_agents_and_human_approval_gate(self, chat, route, memories):
        chat.side_effect = [
            {"answer": "Plan", "model": "test-model"},
            {"answer": "Evidence analysis", "model": "test-model"},
            {"answer": "Recommendation", "model": "test-model"},
        ]
        result = roaming_ai.run_roaming_task("Review a service outage", "workspace-a")
        self.assertEqual(result["status"], "proposal_ready")
        self.assertEqual([x["agent"] for x in result["agents"]], ["planner", "researcher", "arbiter"])
        self.assertEqual(len(result["checkpoints"]), 4)
        self.assertFalse(result["execution"]["performed"])
        self.assertEqual(result["execution"]["reason"], "human_approval_required")
        self.assertEqual(result["evidence"]["memories"][0]["id"], "m1")
        self.assertEqual(chat.call_count, 3)
        route.assert_called_once_with("Review a service outage")
        memories.assert_called_once_with("Review a service outage", "workspace-a", limit=3)

    @patch("xparallel.roaming_ai.chat_with_ai", side_effect=RuntimeError("provider unavailable"))
    def test_provider_failure_is_not_silently_hidden(self, chat):
        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            roaming_ai.run_roaming_task("Investigate a failed task")


if __name__ == "__main__":
    unittest.main()
