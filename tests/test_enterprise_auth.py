import unittest
import time
import os

from xparallel.enterprise_auth import authorize_enterprise_request, required_action
from xparallel.tenant_identity import issue_identity_token

SECRET = "enterprise-test-secret-at-least-thirty-two-bytes"


class EnterpriseAuthTests(unittest.TestCase):
    def setUp(self):
        self.secret = SECRET
        self.old_secret = os.environ.get('XP_IDENTITY_SIGNING_SECRET')
        os.environ['XP_IDENTITY_SIGNING_SECRET'] = self.secret

    def tearDown(self):
        if self.old_secret is None:
            os.environ.pop('XP_IDENTITY_SIGNING_SECRET', None)
        else:
            os.environ['XP_IDENTITY_SIGNING_SECRET'] = self.old_secret

    def token(self, role="operator", workspace="trusted-workspace", actor="human-7"):
        return issue_identity_token(
            subject=actor, workspace_id=workspace, role=role,
            secret=self.secret, now=int(time.time()),
        )

    def test_enterprise_routes_require_separate_identity_header(self):
        context, error = authorize_enterprise_request({}, "POST", "/api/omni/records")
        self.assertIsNone(context)
        self.assertEqual(error, "unauthorized")

    def test_client_workspace_and_actor_are_not_used(self):
        token = self.token()
        headers = {
            "X-Enterprise-Identity": token,
            "X-Workspace-ID": "attacker-workspace",
            "X-Actor": "attacker",
        }
        context, error = authorize_enterprise_request(headers, "POST", "/api/omni/records")
        self.assertIsNone(error)
        self.assertEqual(context["workspace_id"], "trusted-workspace")
        self.assertEqual(context["actor"], "human-7")

    def test_viewer_cannot_create_records(self):
        context, error = authorize_enterprise_request(
            {"X-Enterprise-Identity": self.token(role="viewer")},
            "POST", "/api/omni/records",
        )
        self.assertIsNone(context)
        self.assertEqual(error, "forbidden")

    def test_only_owner_can_approve_execution(self):
        context, error = authorize_enterprise_request(
            {"X-Enterprise-Identity": self.token(role="admin")},
            "POST", "/api/elle/tasks/ELLE-T-1/approve",
        )
        self.assertIsNone(context)
        self.assertEqual(error, "forbidden")

    def test_service_routes_keep_existing_auth_boundary(self):
        self.assertIsNone(required_action("GET", "/providers"))
        self.assertIsNone(required_action("POST", "/roaming/heartbeat"))

    def test_tampered_identity_is_rejected(self):
        token = self.token()
        parts = token.split(".")
        parts[2] = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        bad = ".".join(parts)
        context, error = authorize_enterprise_request(
            {"X-Enterprise-Identity": bad}, "GET", "/api/omni/search",
        )
        self.assertIsNone(context)
        self.assertEqual(error, "unauthorized")


if __name__ == "__main__":
    unittest.main()
