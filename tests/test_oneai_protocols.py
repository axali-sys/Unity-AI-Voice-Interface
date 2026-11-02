import unittest
from unittest.mock import patch
from xparallel import interoperability_protocol as interop
from xparallel import parallel_intelligence as parallel

class ProtocolTests(unittest.TestCase):
    def test_agent_passport_does_not_expose_credentials(self):
        passport = interop.agent_passport({
            "runtime_id":"worker-a","name":"Worker A","base_url":"https://worker.example",
            "capabilities":["chat"],"status":"online","runtime_token":"SECRET"
        })
        self.assertEqual(passport["agent_id"],"worker-a")
        self.assertFalse(passport["credential_disclosed"])
        self.assertNotIn("runtime_token",passport)

    def test_dispatch_requires_approval_and_allowlist(self):
        with self.assertRaises(PermissionError):
            interop.dispatch_approved_task("worker-a","chat",{},"ws",approved=False)
        with self.assertRaises(ValueError):
            interop.dispatch_approved_task("worker-a","shell.exec",{},"ws",approved=True)

    def test_parallel_status_does_not_claim_consensus(self):
        with patch.object(parallel,"configured_providers",return_value=[]):
            status=parallel.capability_status()
        self.assertFalse(status["multi_model_consensus_available"])
        self.assertEqual(status["configured_provider_count"],0)

if __name__ == "__main__":
    unittest.main()
