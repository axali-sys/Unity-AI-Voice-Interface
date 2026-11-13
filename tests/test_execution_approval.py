import hashlib
import tempfile
import unittest
from pathlib import Path

from xparallel.execution_approval import ExecutionApprovalRegistry


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


class ExecutionApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.current_ok = True
        self.registry = ExecutionApprovalRegistry(
            authenticate=lambda session: {
                "requester": {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-a"},
                "approver": {"authenticated": True, "subject": "reviewer:1", "workspace_id": "ws-a"},
                "reviewer": {"authenticated": True, "subject": "reviewer:1", "workspace_id": "ws-a"},
                "executor": {"authenticated": True, "subject": "worker:1", "workspace_id": "ws-a"},
                "outsider": {"authenticated": True, "subject": "outsider:1", "workspace_id": "ws-b"},
            }.get(session, {"authenticated": False}),
            authorize_request=lambda principal, intent: principal["subject"] == "owner:1",
            authorize_approval=lambda principal, intent: principal["subject"] == "reviewer:1",
            authorize_cancel=lambda principal, intent: principal["subject"] in {"owner:1", "reviewer:1"},
            authorize_executor=lambda principal, intent: principal["subject"] == "worker:1",
            validate_current_state=lambda principal, intent, stage: self.current_ok,
            verify_receipt_commit=lambda session, principal, intent_id, receipt_hash: receipt_hash == "a" * 64,
            db_path=str(Path(self.temp.name) / "approvals.sqlite3"),
        )
        self.limits = {
            "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
            "pids": 32, "output_bytes": 100000,
        }

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def request(self):
        return self.registry.request_intent(
            "requester", entity_id="entity-1234", key_id="key-a",
            capability_id="code.run", action="execute", resource_scope="workspace:project-1",
            payload_digest=sha("payload"), artifact_digest=sha("artifact"),
            runner_image_digest=sha("runner-image"), limits=self.limits,
        )

    def approve(self, intent):
        return self.registry.approve(
            "approver", intent["intent_id"], reason="Reviewed exact job and scope"
        )

    def test_approval_is_separate_and_ticket_is_one_time(self):
        intent = self.request()
        with self.assertRaises(PermissionError):
            self.registry.approve("requester", intent["intent_id"], reason="self approve")
        approved = self.approve(intent)
        self.assertEqual(approved["intent"]["status"], "approved")
        running = self.registry.start("executor", approved["one_time_ticket"])
        self.assertEqual(running["status"], "running")
        with self.assertRaises(PermissionError):
            self.registry.start("executor", approved["one_time_ticket"])

    def test_exact_intent_binds_payload_artifact_runner_and_limits(self):
        intent = self.request()
        self.assertEqual(intent["intent"]["payload_digest"], sha("payload"))
        self.assertEqual(intent["intent"]["artifact_digest"], sha("artifact"))
        self.assertEqual(intent["intent"]["runner_image_digest"], sha("runner-image"))
        self.assertEqual(intent["intent"]["limits"], self.limits)

    def test_revocation_is_checked_before_start(self):
        intent = self.request()
        approved = self.approve(intent)
        self.current_ok = False
        with self.assertRaises(PermissionError):
            self.registry.start("executor", approved["one_time_ticket"])
        self.assertEqual(self.registry.get("requester", intent["intent_id"])["status"], "approved")

    def test_revocation_during_execution_blocks_checkpoint(self):
        intent = self.request()
        approved = self.approve(intent)
        running = self.registry.start("executor", approved["one_time_ticket"])
        self.current_ok = False
        check = self.registry.check_running("executor", running["intent_id"])
        self.assertFalse(check["continue"])
        self.assertEqual(check["reason"], "execution_revoked_or_stale")

    def test_revocation_blocks_successful_completion(self):
        intent = self.request()
        approved = self.approve(intent)
        running = self.registry.start("executor", approved["one_time_ticket"])
        self.current_ok = False
        with self.assertRaises(PermissionError):
            self.registry.finish("executor", running["intent_id"], outcome="success")

    def test_executor_identity_is_bound_and_finish_is_terminal(self):
        intent = self.request()
        approved = self.approve(intent)
        running = self.registry.start("executor", approved["one_time_ticket"])
        with self.assertRaises(PermissionError):
            self.registry.check_running("requester", running["intent_id"])
        finished = self.registry.finish("executor", running["intent_id"], outcome="success")
        self.assertEqual(finished["status"], "completed")
        with self.assertRaises(ValueError):
            self.registry.finish("executor", running["intent_id"], outcome="success")

    def test_finalization_is_nonterminal_until_receipt_commit(self):
        intent = self.request()
        approved = self.approve(intent)
        running = self.registry.start("executor", approved["one_time_ticket"])
        pending = self.registry.begin_finalization("executor", running["intent_id"], outcome="success", receipt_data={
            "policy_decision": {"allowed": True, "grant_id": "grant:1", "evidence_run_id": "run:1"},
            "started_at": running["started_at"],
            "resource_usage": {"wall_ms": 1, "cpu_ms": 1, "memory_peak_mb": 1, "output_bytes": 1, "pids_peak": 1},
            "evidence_refs": ["evidence:one"],
        })
        self.assertEqual(pending["status"], "finalizing")
        self.assertIsNotNone(pending["finished_at"])
        recovered = self.registry.get_finalization_for_recovery("executor", running["intent_id"])
        self.assertEqual(recovered["finalization_data"]["evidence_refs"], ["evidence:one"])
        with self.assertRaises(PermissionError):
            self.registry.get_finalization_for_recovery("requester", running["intent_id"])
        self.assertEqual(self.registry.get("requester", running["intent_id"])["status"], "finalizing")
        self.assertNotIn("finalization_data", self.registry.get("requester", running["intent_id"]))
        completed = self.registry.complete_finalization("executor", running["intent_id"], receipt_hash="a" * 64)
        self.assertEqual(completed["status"], "completed")
        with self.assertRaises(ValueError):
            self.registry.complete_finalization("executor", running["intent_id"])

    def test_terminal_transition_fails_closed_without_verified_receipt(self):
        intent = self.request()
        approved = self.approve(intent)
        running = self.registry.start("executor", approved["one_time_ticket"])
        self.registry.begin_finalization("executor", running["intent_id"], outcome="failure")
        self.registry._verify_receipt_commit = lambda principal, intent_id, receipt_hash: False
        with self.assertRaises(PermissionError):
            self.registry.complete_finalization("executor", running["intent_id"], receipt_hash="a" * 64)
        self.assertEqual(self.registry.get("requester", running["intent_id"])["status"], "finalizing")

    def test_cancellation_invalidates_ticket_and_stops_running_state(self):
        intent = self.request()
        approved = self.approve(intent)
        cancelled = self.registry.cancel("reviewer", intent["intent_id"], reason="Safety review")
        self.assertEqual(cancelled["status"], "cancelled")
        with self.assertRaises(PermissionError):
            self.registry.start("executor", approved["one_time_ticket"])

    def test_workspace_isolation_and_executor_authority(self):
        intent = self.request()
        approved = self.approve(intent)
        with self.assertRaises(PermissionError):
            self.registry.start("outsider", approved["one_time_ticket"])
        with self.assertRaises(PermissionError):
            self.registry.request_intent(
                "outsider", entity_id="entity-1234", key_id="key-a",
                capability_id="code.run", action="execute", resource_scope="workspace:project-1",
                payload_digest=sha("payload"), artifact_digest=sha("artifact"),
                runner_image_digest=sha("runner-image"), limits=self.limits,
            )

    def test_invalid_limits_and_wildcard_scope_are_rejected(self):
        with self.assertRaises(ValueError):
            self.registry.request_intent(
                "requester", entity_id="entity-1234", key_id="key-a",
                capability_id="code.run", action="execute", resource_scope="*",
                payload_digest=sha("payload"), artifact_digest=sha("artifact"),
                runner_image_digest=sha("runner-image"),
                limits={**self.limits, "timeout_seconds": 9999},
            )

    def test_event_history_records_request_approval_start_and_finish(self):
        intent = self.request()
        approved = self.approve(intent)
        running = self.registry.start("executor", approved["one_time_ticket"])
        self.registry.finish("executor", running["intent_id"], outcome="success")
        events = self.registry.events("requester", intent["intent_id"])
        self.assertEqual(
            [event["event_type"] for event in events],
            ["intent_requested", "intent_approved", "execution_started", "execution_success"],
        )


if __name__ == "__main__":
    unittest.main()
