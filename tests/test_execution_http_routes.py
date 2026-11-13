import unittest
from unittest.mock import patch

from xparallel import server


class Handler:
    def __init__(self, claims=None):
        self.identity_context = claims\n        self.headers = {"Authorization": "Bearer verified-token"}
        self.response = None


def capture(handler, status, payload, cors=False):
    handler.response = (status, payload)


class FakeAPI:
    def __init__(self):
        self.calls = []

    def request_intent(self, claims, data, *, session_token):
        self.calls.append(("request", claims, data, session_token))
        return {"intent": {"status": "requested"}}

    def approve_intent(self, claims, data, *, session_token):
        self.calls.append(("approve", claims, data, session_token))
        return {"approval": {"status": "approved"}}

    def execute_ticket(self, claims, data, *, session_token):
        self.calls.append(("execute", claims, data, session_token))
        return {"status": "completed"}

    def recover_pending(self, claims, data, *, session_token):
        self.calls.append(("recover", claims, data, session_token))
        return {"pending": 0}


class ExecutionHTTPRouteTests(unittest.TestCase):
    def setUp(self):
        self.handler = Handler({
            "authenticated": True, "subject": "operator:1",
            "workspace_id": "workspace-a", "role": "operator",
        })
        self.api = FakeAPI()

    def test_unrelated_route_is_not_handled(self):
        with patch.object(server, "send_json", side_effect=capture):
            self.assertFalse(server.dispatch_execution_post(self.handler, "/chat", {}))
        self.assertIsNone(self.handler.response)

    def test_shared_token_mode_fails_closed(self):
        with patch.object(server, "AUTH_MODE", "legacy"), \
             patch.object(server, "SESSION_VERIFIER", None), \
             patch.object(server, "EXECUTION_API", self.api), \
             patch.object(server, "send_json", side_effect=capture):
            self.assertTrue(server.dispatch_execution_post(self.handler, "/execution/run", {"one_time_ticket": "t"}))
        self.assertEqual(self.handler.response[0], 503)
        self.assertEqual(self.handler.response[1]["error"], "trusted_execution_identity_unavailable")
        self.assertEqual(self.api.calls, [])

    def test_jwt_without_host_bootstrap_fails_closed(self):
        with patch.object(server, "AUTH_MODE", "jwt"), \
             patch.object(server, "SESSION_VERIFIER", object()), \
             patch.object(server, "EXECUTION_API", None), \
             patch.object(server, "send_json", side_effect=capture):
            server.dispatch_execution_post(self.handler, "/execution/intents", {})
        self.assertEqual(self.handler.response[0], 503)
        self.assertEqual(self.handler.response[1]["error"], "trusted_execution_host_not_configured")

    def test_all_private_routes_dispatch_with_verified_claims(self):
        cases = [
            ("/execution/intents", {}, 201, "request"),
            ("/execution/approve", {}, 200, "approve"),
            ("/execution/run", {"one_time_ticket": "ticket"}, 200, "execute"),
            ("/execution/recover", {"limit": 10}, 200, "recover"),
        ]
        with patch.object(server, "AUTH_MODE", "jwt"), \
             patch.object(server, "SESSION_VERIFIER", object()), \
             patch.object(server, "EXECUTION_API", self.api), \
             patch.object(server, "send_json", side_effect=capture):
            for path, body, status, operation in cases:
                self.handler.response = None
                self.assertTrue(server.dispatch_execution_post(self.handler, path, body))
                self.assertEqual(self.handler.response[0], status)
                self.assertEqual(self.api.calls[-1][0], operation)
                self.assertEqual(self.api.calls[-1][1]["workspace_id"], "workspace-a")\n                self.assertEqual(self.api.calls[-1][3], "verified-token")

    def test_permission_and_validation_errors_are_mapped_safely(self):
        class DeniedAPI(FakeAPI):
            def execute_ticket(self, claims, data, *, session_token):
                raise PermissionError("execution_role_not_authorized")
        with patch.object(server, "AUTH_MODE", "jwt"), \
             patch.object(server, "SESSION_VERIFIER", object()), \
             patch.object(server, "EXECUTION_API", DeniedAPI()), \
             patch.object(server, "send_json", side_effect=capture):
            server.dispatch_execution_post(self.handler, "/execution/run", {"one_time_ticket": "x"})
        self.assertEqual(self.handler.response, (403, {"error": "execution_role_not_authorized"}))


if __name__ == "__main__":
    unittest.main()
