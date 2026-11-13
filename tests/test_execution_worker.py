import hashlib
import unittest

from xparallel.execution_worker import ApprovedExecutionWorker, _canonical_digest


class FakeApprovals:
    def __init__(self, intent, checkpoint=True):
        self.intent = intent
        self.checkpoint_allowed = checkpoint
        self.finished = None

    def start(self, session, ticket):
        if ticket != "one-use-ticket":
            raise PermissionError("invalid_execution_ticket")
        return {"intent_id": "job:123", "intent": self.intent, "started_at": "2026-11-13T10:00:00+00:00"}

    def check_running(self, session, intent_id):
        return {"continue": self.checkpoint_allowed}

    def finish(self, session, intent_id, *, outcome):
        self.finished = outcome
        return {
            "intent_id": intent_id, "status": "completed" if outcome == "success" else "failed",
            "started_at": "2026-11-13T10:00:00+00:00",
            "finished_at": "2026-11-13T10:00:02+00:00",
        }


class FakeReceipts:
    def __init__(self):
        self.record = None

    def append(self, session, **kwargs):
        self.record = kwargs
        return {"receipt_hash": "a" * 64, "receipt": {"intent_id": kwargs["intent_id"]}}


class ApprovedExecutionWorkerTests(unittest.TestCase):
    def setUp(self):
        self.payload = {"files": {"main.py": "cHJpbnQoJ29rJyk="}, "test_profile": "python-unittest"}
        self.intent = {
            "payload_digest": _canonical_digest(self.payload),
            "artifact_digest": hashlib.sha256(b"artifact").hexdigest(),
            "runner_image_digest": "b" * 64,
            "limits": {"timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
                       "pids": 32, "output_bytes": 4096},
        }
        self.approvals = FakeApprovals(self.intent)
        self.receipts = FakeReceipts()
        self.runner_calls = []
        self.worker = ApprovedExecutionWorker(
            approvals=self.approvals,
            runner=lambda payload, **kwargs: self.runner_calls.append((payload, kwargs)) or {
                "status": "success", "output_bytes": 12,
            },
            load_payload=lambda intent: self.payload,
            resolve_artifact_digest=lambda intent: self.intent["artifact_digest"],
            resolve_policy_evidence=lambda intent: {
                "allowed": True, "grant_id": "grant:1", "evidence_run_id": "run:1",
            },
            measure_resources=lambda result, intent: {
                "wall_ms": 2000, "cpu_ms": 100, "memory_peak_mb": 64,
                "output_bytes": 12, "pids_peak": 1,
            },
            store_evidence=lambda result, intent: ["evidence:execution:123"],
            receipts=self.receipts,
        )

    def test_valid_ticket_runs_with_pinned_intent_and_creates_receipt(self):
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["outcome"], "success")
        self.assertEqual(self.approvals.finished, "success")
        self.assertEqual(len(self.runner_calls), 1)
        _, kwargs = self.runner_calls[0]
        self.assertEqual(kwargs["approved_limits"], self.intent["limits"])
        self.assertEqual(kwargs["expected_image_digest"], self.intent["runner_image_digest"])
        self.assertEqual(self.receipts.record["exit_code"], 0)

    def test_payload_tampering_blocks_runner(self):
        self.payload = {"files": {"main.py": "YXR0YWNr"}, "test_command": "sh"}
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(self.approvals.finished, "blocked")
        self.assertEqual(self.runner_calls, [])

    def test_artifact_digest_mismatch_blocks_runner(self):
        self.worker._resolve_artifact = lambda intent: "0" * 64
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(self.runner_calls, [])

    def test_revocation_before_start_blocks_runner(self):
        self.approvals.checkpoint_allowed = False
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["outcome"], "blocked")
        self.assertEqual(self.runner_calls, [])

    def test_invalid_ticket_never_launches_runner(self):
        with self.assertRaisesRegex(PermissionError, "invalid_execution_ticket"):
            self.worker.execute("worker-session", "wrong-ticket")
        self.assertEqual(self.runner_calls, [])


if __name__ == "__main__":
    unittest.main()
