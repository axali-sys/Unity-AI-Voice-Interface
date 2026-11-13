import hashlib
import unittest

from xparallel.trusted_execution import TrustedExecutionControlPlane


class FakeGate:
    def __init__(self, authenticate, host):
        self.authenticate = authenticate
        self.host = host

    def authorize(self, session, **kwargs):
        principal = self.authenticate(session)
        if principal.get("authenticated") is not True:
            return {"allowed": False, "reason": "caller_not_authenticated"}
        return {
            "allowed": self.host.allowed
            and principal.get("workspace_id") == "workspace-a"
            and kwargs.get("entity_id") == "entity-a"
            and kwargs.get("capability_id") == "capability.read"
            and kwargs.get("resource_scope") == "document:7",
            "reason": "verified" if self.host.allowed else "revoked",
        }


class FakeTrustedHost:
    def __init__(self):
        self.allowed = True
        self.sessions = {
            "owner-session": {"authenticated": True, "subject": "owner:1", "workspace_id": "workspace-a"},
            "approver-session": {"authenticated": True, "subject": "admin:1", "workspace_id": "workspace-a"},
            "worker-session": {"authenticated": True, "subject": "worker:1", "workspace_id": "workspace-a"},
        }

    def authenticate(self, session):
        return self.sessions.get(session, {"authenticated": False})

    def resolve_entity_context(self, principal, entity_id, key_id, capability_id):
        if (principal.get("workspace_id"), entity_id, key_id, capability_id) != (
            "workspace-a", "entity-a", "key-a", "capability.read"
        ):
            return None
        return {"artifact_digest": hashlib.sha256(b"artifact-v1").hexdigest()}

    def load_active_grants(self, principal, entity_id):
        return [{"grant_id": "grant-1"}] if self.allowed else []

    def build_action_gate(self, *, authenticate=None):
        return FakeGate(authenticate or self.authenticate, self)


class TrustedExecutionControlPlaneTests(unittest.TestCase):
    def setUp(self):
        self.host = FakeTrustedHost()
        self.control = TrustedExecutionControlPlane(
            trusted_host=self.host,
            authorize_approval=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_cancel=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_executor=lambda principal, intent: principal["subject"] == "worker:1",
            db_path=":memory:",
        )
        self.limits = {
            "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
            "pids": 32, "output_bytes": 100000,
        }

    def tearDown(self):
        self.control.close()

    def request(self, artifact=None):
        return self.control.approvals.request_intent(
            "owner-session",
            entity_id="entity-a", key_id="key-a",
            capability_id="capability.read", action="read",
            resource_scope="document:7",
            payload_digest=hashlib.sha256(b"payload").hexdigest(),
            artifact_digest=artifact or hashlib.sha256(b"artifact-v1").hexdigest(),
            runner_image_digest=hashlib.sha256(b"runner").hexdigest(),
            limits=self.limits,
        )

    def test_trusted_gate_allows_immutable_intent_and_separate_approval(self):
        intent = self.request()
        self.assertEqual(intent["status"], "requested")
        approved = self.control.approvals.approve(
            "approver-session", intent["intent_id"], reason="Independent approval"
        )
        self.assertEqual(approved["intent"]["status"], "approved")
        running = self.control.approvals.start(
            "worker-session", approved["one_time_ticket"]
        )
        self.assertEqual(running["status"], "running")

    def test_untrusted_artifact_digest_is_rejected_before_intent_creation(self):
        with self.assertRaisesRegex(PermissionError, "execution_intent_not_authorized"):
            self.request(hashlib.sha256(b"attacker-artifact").hexdigest())

    def test_permission_revocation_blocks_worker_checkpoint(self):
        intent = self.request()
        approved = self.control.approvals.approve(
            "approver-session", intent["intent_id"], reason="Approved"
        )
        self.control.approvals.start("worker-session", approved["one_time_ticket"])
        self.host.allowed = False
        checkpoint = self.control.approvals.check_running(
            "worker-session", intent["intent_id"]
        )
        self.assertFalse(checkpoint["continue"])
        self.assertEqual(checkpoint["reason"], "execution_revoked_or_stale")

    def test_requester_cannot_approve_own_execution(self):
        intent = self.request()
        with self.assertRaisesRegex(PermissionError, "requester_cannot_approve_own_execution"):
            self.control.approvals.approve(
                "owner-session", intent["intent_id"], reason="Self approval"
            )

    def test_untrusted_executor_cannot_consume_ticket(self):
        intent = self.request()
        approved = self.control.approvals.approve(
            "approver-session", intent["intent_id"], reason="Approved"
        )
        with self.assertRaisesRegex(PermissionError, "executor_not_authorized"):
            self.control.approvals.start("owner-session", approved["one_time_ticket"])


if __name__ == "__main__":
    unittest.main()
