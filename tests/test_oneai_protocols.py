import unittest
from unittest.mock import patch
from xparallel import interoperability_protocol as interop
from xparallel import parallel_intelligence as parallel


class ProtocolTests(unittest.TestCase):
    def test_agent_passport_does_not_expose_credentials(self):
        passport = interop.agent_passport({
            "runtime_id": "worker-a", "name": "Worker A",
            "base_url": "https://worker.example", "capabilities": ["chat"],
            "status": "online", "runtime_token": "SECRET"
        })
        self.assertEqual(passport["agent_id"], "worker-a")
        self.assertFalse(passport["credential_disclosed"])
        self.assertNotIn("runtime_token", passport)

    def test_dispatch_requires_approval_and_allowlist(self):
        with self.assertRaises(PermissionError):
            interop.dispatch_approved_task("worker-a", "chat", {}, "ws", approved=False)
        with self.assertRaises(ValueError):
            interop.dispatch_approved_task("worker-a", "shell.exec", {}, "ws", approved=True)

    def test_parallel_status_does_not_claim_consensus_without_two_providers(self):
        with patch.object(parallel, "_provider_slots", return_value=[]):
            status = parallel.capability_status()
            result = parallel.research("Compare two approaches")
        self.assertFalse(status["multi_model_consensus_available"])
        self.assertFalse(status["independent_panel_available"])
        self.assertEqual(status["configured_provider_count"], 0)
        self.assertEqual(result["collaboration_status"], "not_available")
        self.assertFalse(result["execution_performed"])

    def test_parallel_calls_each_provider_independently(self):
        providers = [
            {"id": "one", "endpoint": "https://one.example/v1/chat/completions", "key": "k1", "model": "m1"},
            {"id": "two", "endpoint": "https://two.example/v1/chat/completions", "key": "k2", "model": "m2"},
        ]
        with patch.object(parallel, "_provider_slots", return_value=providers), \
             patch.object(parallel, "_invoke", side_effect=[
                 {"provider_id": "one", "model": "m1", "response": "Finding A", "status": "completed"},
                 {"provider_id": "two", "model": "m2", "response": "Finding B", "status": "completed"},
             ]) as invoke:
            result = parallel.research("Research this", "workspace-a")
        self.assertEqual(invoke.call_count, 2)
        self.assertEqual(result["mode"], "independent_multi_model_panel")
        self.assertFalse(result["comparison"]["consensus_claimed"])
        self.assertEqual(result["comparison"]["response_count"], 2)

    def test_parallel_rejects_empty_query(self):
        with self.assertRaises(ValueError):
            parallel.research("")


if __name__ == "__main__":
    unittest.main()
