import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from xparallel.parallel_world import create_parallel_plan


class ParallelWorldPlannerTests(unittest.TestCase):
    @patch("xparallel.parallel_world.search_memories", return_value=[])
    def test_missing_provider_key_fails_explicitly(self, _search):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "ai_provider_not_configured"):
                create_parallel_plan("Fix a failing service", "workspace-a")

    @patch("xparallel.parallel_world.urlopen")
    @patch("xparallel.parallel_world.search_memories", return_value=[{"id": "mem-1", "summary": "preserve routes", "content": "Keep existing routes", "tags": ["decision"]}])
    def test_returns_plan_and_keeps_human_approval_gate(self, _search, open_url):
        plan = {
            "summary": "Inspect and test the service",
            "steps": ["Inspect repository", "Reproduce failure", "Test minimal fix"],
            "test_strategy": ["Run unit tests"],
            "transfer_gate": "human_approval_required",
            "memory_sources": ["mem-1"],
        }
        response = {"choices": [{"message": {"content": json.dumps(plan)}}]}
        open_url.return_value.__enter__.return_value = BytesIO(json.dumps(response).encode())
        with patch.dict(os.environ, {"XP_AI_API_KEY": "test-only", "XP_AI_MODEL": "test-model"}):
            result = create_parallel_plan("Fix a failing service", "workspace-a")
        self.assertEqual(result["plan"]["execution_status"], "planned_not_executed")
        self.assertEqual(result["plan"]["transfer_gate"], "human_approval_required")
        self.assertEqual(result["plan"]["memory_sources"], ["mem-1"])
        self.assertEqual(open_url.call_args.args[0].get_header("Authorization"), "Bearer test-only")


if __name__ == "__main__":
    unittest.main()
