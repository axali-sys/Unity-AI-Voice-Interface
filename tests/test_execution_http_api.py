import unittest

from xparallel.execution_http_api import ExecutionHTTPAPI


class FakeApprovals:
    def __init__(self):
        self.calls = []

    def request_intent(self, session, **body):
        self.calls.append(("request", session, body))
        return {"intent_id": "job:1", "status": "requested"}

    def approve(self, session, intent_id, *, reason):
        self.calls.append(("approve", session, intent_id, reason))
        return {"intent_id": intent_id, "one_time_ticket": "secret-ticket"}

class FakeWorker:
    def __init__(self):
        self.calls = []

    def execute(self, session, ticket):
        self.calls.append(("execute", session, ticket))
        return {"status": "completed"}

    def recover_pending_finalizations(self, session, *, limit):
        self.calls.append(("recover", session, limit))
        return {"scanned": 0, "recovered": 0, "pending": 0, "results": []}

class FakeHostServices:
    def __init__(self, approvals):
        self.approvals = approvals
    def build_worker(self):
        return WORKER

WORKER = FakeWorker()

class ExecutionHTTPAPITests(unittest.TestCase):
    def setUp(self):
        self.approvals = FakeApprovals()
        self.api = ExecutionHTTPAPI(
            control_plane=type("Control", (), {"approvals": self.approvals})(),
            host_services=FakeHostServices(self.approvals),
        )
        self.owner = {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-a", "role": "owner"}
        self.admin = {"authenticated": True, "subject": "admin:1", "workspace_id": "ws-a", "role": "admin"}
        self.operator = {"authenticated": True, "subject": "worker:1", "workspace_id": "ws-a", "role": "operator"}

    def test_request_uses_verified_principal_not_body_tenant(self):
        body = {
            "entity_id": "entity-a", "key_id": "key-a", "capability_id": "cap.read",
            "action": "read", "resource_scope": "document:1",
            "payload_digest": "a" * 64, "artifact_digest": "b" * 64,
            "runner_image_digest": "c" * 64,
            "limits": {"timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000, "pids": 32, "output_bytes": 4096},
        }
        result = self.api.request_intent(self.owner, body, session_token='signed-owner-token')
        self.assertEqual(result["intent"]["status"], "requested")
        self.assertEqual(self.approvals.calls[0][1], "signed-owner-token")

    def test_rejects_body_identity_overrides_and_unknown_fields(self):
        body = {"workspace_id": "other", "actor": "attacker"}
        with self.assertRaisesRegex(ValueError, "schema_mismatch"):
            self.api.request_intent(self.owner, body, session_token='signed-owner-token')

    def test_viewer_cannot_request_execution(self):
        viewer = {**self.owner, "role": "viewer"}
        with self.assertRaisesRegex(PermissionError, "role_not_authorized"):
            self.api.request_intent(viewer, {}, session_token='bad')

    def test_approver_receives_ticket_but_requester_cannot_self_approve_in_registry(self):
        result = self.api.approve_intent(self.admin, {"intent_id": "job:1", "reason": "reviewed"}, session_token='signed-admin-token')
        self.assertEqual(result["approval"]["one_time_ticket"], "secret-ticket")

    def test_only_operator_can_execute_and_recover(self):
        with self.assertRaisesRegex(PermissionError, "role_not_authorized"):
            self.api.execute_ticket(self.owner, {"one_time_ticket": "x"}, session_token='bad')
        self.assertEqual(self.api.execute_ticket(self.operator, {"one_time_ticket": "x"}, session_token='signed-operator-token')["status"], "completed")
        self.assertEqual(self.api.recover_pending(self.operator, {"limit": 10}, session_token='signed-operator-token')["scanned"], 0)

    def test_host_components_must_share_approval_registry(self):
        with self.assertRaisesRegex(TypeError, "share_approval_registry"):
            ExecutionHTTPAPI(
                control_plane=type("Control", (), {"approvals": self.approvals})(),
                host_services=FakeHostServices(FakeApprovals()),
            )

if __name__ == "__main__":
    unittest.main()
