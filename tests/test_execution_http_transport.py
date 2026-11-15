"""End-to-end HTTP transport tests for the private XParallel execution routes.

These tests exercise BaseHTTPRequestHandler over a real loopback HTTPServer.
The verifier and host API are test doubles; JWT cryptography and execution
lifecycle are covered by their dedicated unit/integration suites.
"""
import http.client
import json
import threading
import unittest
from unittest.mock import patch

from http.server import HTTPServer
from xparallel import server


TOKEN = "loopback-test-session"
CLAIMS = {
    "authenticated": True,
    "subject": "operator:loopback",
    "workspace_id": "workspace-loopback",
    "role": "operator",
}


class FakeExecutionAPI:
    def __init__(self):
        self.calls = []

    def recovery_health(self, claims):
        self.calls.append(("health", claims))
        return {"recovery": {"running": False, "total_failures": 0}}

    def request_intent(self, claims, data, *, session_token):
        self.calls.append(("request", claims, data, session_token))
        return {"intent": {"status": "requested"}}


class QuietHandler(server.Handler):
    def log_message(self, format, *args):
        pass


class ExecutionHTTPTransportTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeExecutionAPI()
        self.patches = [
            patch.object(server, "AUTH_MODE", "jwt"),
            patch.object(
                server, "SESSION_VERIFIER",
                lambda token: CLAIMS if token == TOKEN else (_ for _ in ()).throw(PermissionError("invalid")),
            ),
            patch.object(server, "EXECUTION_API", self.api),
        ]
        for item in self.patches:
            item.start()
        self.httpd = HTTPServer(("127.0.0.1", 0), QuietHandler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)
        for item in reversed(self.patches):
            item.stop()

    def _request(self, method, path, body=None, token=TOKEN):
        connection = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        headers = {}
        payload = None
        if body is not None:
            payload = json.dumps(body)
            headers["Content-Type"] = "application/json"
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        connection.request(method, path, body=payload, headers=headers)
        response = connection.getresponse()
        result = (response.status, json.loads(response.read() or b"{}"))
        connection.close()
        return result

    def test_private_health_route_requires_a_verified_session(self):
        status, payload = self._request("GET", "/execution/health", token=None)
        self.assertEqual(status, 401)
        self.assertEqual(payload["error"], "unauthorized")
        self.assertEqual(self.api.calls, [])

        status, payload = self._request("GET", "/execution/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload["recovery"]["running"], False)
        self.assertEqual(self.api.calls[0], ("health", CLAIMS))

    def test_intent_route_binds_verified_claims_and_original_session_token(self):
        body = {"entity_id": "entity-a", "capability_id": "capability.read"}
        status, payload = self._request("POST", "/execution/intents", body)
        self.assertEqual(status, 201)
        self.assertEqual(payload["intent"]["status"], "requested")
        operation, claims, received_body, session_token = self.api.calls[0]
        self.assertEqual(operation, "request")
        self.assertEqual(claims, CLAIMS)
        self.assertEqual(received_body, body)
        self.assertEqual(session_token, TOKEN)


if __name__ == "__main__":
    unittest.main()
