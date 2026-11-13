import hashlib
import unittest

from xparallel.execution_worker import ApprovedExecutionWorker, _canonical_digest


class FakeApprovals:
    def __init__(self, intent, checkpoint=True):
        self.intent = intent
        self.checkpoint_allowed = checkpoint
        self.finished = None
        self.finalizing = None
        self.finalization_data = None

    def start(self, session, ticket):
        if ticket != "one-use-ticket":
            raise PermissionError("invalid_execution_ticket")
        return {"intent_id": "job:123", "intent": self.intent, "started_at": "2026-11-13T10:00:00+00:00"}

    def check_running(self, session, intent_id):
        return {"continue": self.checkpoint_allowed}

    def begin_finalization(self, session, intent_id, *, outcome):
        self.finalizing = outcome
        return {
            "intent_id": intent_id, "status": "finalizing", "outcome": outcome,
            "started_at": "2026-11-13T10:00:00+00:00",
            "finished_at": "2026-11-13T10:00:02+00:00",
        }

    def get_finalization_for_recovery(self, session, intent_id):
        return {"intent_id": intent_id, "status": "finalizing", "outcome": self.finalizing,
                "finished_at": "2026-11-13T10:00:02+00:00",
                "finalization_data": self.finalization_data}

    def complete_finalization(self, session, intent_id):
        self.finished = self.finalizing
        return {"intent_id": intent_id,
                "status": "completed" if self.finished == "success" else "failed"}


class FakeReceipts:
    def __init__(self):
        self.record = None
        self.fail = False

    def get_by_intent(self, session, intent_id):
        if self.record is not None and self.record.get("intent_id") == intent_id:
            return {"receipt": {"intent_id": intent_id}, "receipt_hash": "a" * 64}
        return None

    def append(self, session, **kwargs):
        if self.fail:
            raise OSError("receipt store unavailable")
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
        self.assertFalse(result["receipt_pending"])
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

    def test_evidence_failure_prevents_success_terminal_status(self):
        self.worker._store_evidence = lambda result, intent: (_ for _ in ()).throw(OSError("storage offline"))
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["outcome"], "failure")
        self.assertEqual(result["status"], "finalizing")
        self.assertTrue(result["receipt_pending"])
        self.assertIsNone(result["receipt"])
        self.assertEqual(result["error"], "execution_evidence_pipeline_failed")
        self.assertIsNone(self.approvals.finished)
        self.assertEqual(self.approvals.finalizing, "failure")
        self.assertIsNone(self.receipts.record)

    def test_measurement_failure_prevents_success_terminal_status(self):
        self.worker._measure = lambda result, intent: (_ for _ in ()).throw(RuntimeError("meter unavailable"))
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["outcome"], "failure")
        self.assertEqual(result["status"], "finalizing")
        self.assertTrue(result["receipt_pending"])
        self.assertIsNone(result["receipt"])
        self.assertIsNone(self.approvals.finished)
        self.assertEqual(self.approvals.finalizing, "failure")
        self.assertIsNone(self.receipts.record)

    def test_receipt_failure_keeps_job_non_terminal(self):
        self.receipts.fail = True
        result = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(result["status"], "finalizing")
        self.assertTrue(result["receipt_pending"])
        self.assertEqual(result["error"], "execution_receipt_commit_failed")
        self.assertEqual(self.approvals.finalizing, "success")
        self.assertIsNone(self.approvals.finished)

    def test_receipt_failure_can_be_recovered_without_rerunning_code(self):
        self.receipts.fail = True
        pending = self.worker.execute("worker-session", "one-use-ticket")
        self.assertEqual(pending["status"], "finalizing")
        self.receipts.fail = False
        recovered = self.worker.recover_finalization("worker-session", "job:123")
        self.assertTrue(recovered["recovered"])
        self.assertEqual(recovered["status"], "completed")
        self.assertEqual(len(self.runner_calls), 1)
        self.assertEqual(self.receipts.record["intent_id"], "job:123")

    def test_recovery_after_receipt_commit_does_not_append_duplicate(self):
        self.worker.execute("worker-session", "one-use-ticket")
        self.approvals.finished = None
        recovered = self.worker.recover_finalization("worker-session", "job:123")
        self.assertTrue(recovered["recovered"])
        self.assertEqual(recovered["status"], "completed")
        self.assertEqual(len(self.runner_calls), 1)

    def test_invalid_ticket_never_launches_runner(self):
        with self.assertRaisesRegex(PermissionError, "invalid_execution_ticket"):
            self.worker.execute("worker-session", "wrong-ticket")
        self.assertEqual(self.runner_calls, [])


if __name__ == "__main__":
    unittest.main()
