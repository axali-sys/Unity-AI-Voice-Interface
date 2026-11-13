import unittest
from unittest.mock import patch

from xparallel import server


class FakeRegistry:
    def get(self, token, grant_id):
        if token != "trusted-session":
            raise PermissionError("caller_not_authenticated")
        return {"grant_id": grant_id, "status": "approved"}

    def revoke(self, token, grant_id, reason):
        if token != "trusted-session":
            raise PermissionError("caller_not_authenticated")
        if not reason:
            raise ValueError("governance_reason_required")
        return {"grant_id": grant_id, "status": "revoked", "reason": reason}


class FakeHandler:
    headers = {"Authorization": "Bearer trusted-session"}


class GovernanceHTTPDispatchTests(unittest.TestCase):
    def setUp(self):
        self.patches = [
            patch.object(server, "AUTH_MODE", "jwt"),
            patch.object(server, "SESSION_VERIFIER", object()),
            patch.object(server, "ENTITY_GOVERNANCE", FakeRegistry()),
            patch.object(server, "send_json"),
        ]
        for item in self.patches:
            item.start()
        self.addCleanup(self.stop_patches)

    def stop_patches(self):
        for item in reversed(self.patches):
            item.stop()

    def test_get_grant_is_scoped_through_registry(self):
        self.assertTrue(server.dispatch_governance_get(
            FakeHandler(), "/governance/grants/grant:123"
        ))
        server.send_json.assert_called_once()
        args, _ = server.send_json.call_args
        self.assertEqual(args[1:], (200, {"grant": {"grant_id": "grant:123", "status": "approved"}}))

    def test_revoke_requires_exact_schema_and_returns_revoked_state(self):
        payload = {"grant_id": "grant:123", "reason": "Owner requested revocation"}
        self.assertTrue(server.dispatch_governance_post(
            FakeHandler(), "/governance/grants/revoke", payload
        ))
        server.send_json.assert_called_once()
        args, _ = server.send_json.call_args
        self.assertEqual(args[1:], (200, {"grant": {"grant_id": "grant:123", "status": "revoked",
                       "reason": "Owner requested revocation"}, "revoked": True}))

    def test_missing_trusted_registry_fails_closed(self):
        with patch.object(server, "ENTITY_GOVERNANCE", None):
            self.assertTrue(server.dispatch_governance_post(
                FakeHandler(), "/governance/grants/revoke",
                {"grant_id": "grant:123", "reason": "review"}
            ))
        server.send_json.assert_called_once()
        args, _ = server.send_json.call_args
        self.assertEqual(args[1:], (503, {"error": "trusted_governance_adapters_not_configured"}))

    def test_unknown_fields_are_rejected(self):
        self.assertTrue(server.dispatch_governance_post(
            FakeHandler(), "/governance/grants/revoke",
            {"grant_id": "grant:123", "reason": "review", "workspace_id": "attacker"}
        ))
        server.send_json.assert_called_once()
        args, _ = server.send_json.call_args
        self.assertEqual(args[1:], (400, {"error": "governance_request_schema_mismatch"}))


if __name__ == "__main__":
    unittest.main()
