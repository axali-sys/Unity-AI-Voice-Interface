import base64
import hashlib
import hmac
import json
import unittest

from xparallel.execution_http_api import ExecutionHTTPAPI
from xparallel.session_jwt import HS256SessionVerifier
from xparallel.trusted_execution import TrustedExecutionControlPlane


def _segment(value):
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _token(claims, key):
    header = _segment({"alg": "HS256", "typ": "JWT"})
    payload = _segment(claims)
    signing_input = f"{header}.{payload}".encode()
    signature = hmac.new(key, signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


class _Gate:
    def __init__(self, authenticate, host):
        self.authenticate = authenticate
        self.host = host

    def authorize(self, session, **kwargs):
        principal = self.authenticate(session)
        allowed = (
            principal.get("authenticated") is True
            and principal.get("workspace_id") == "workspace-a"
            and kwargs.get("entity_id") == "entity-a"
            and kwargs.get("capability_id") == "capability.read"
            and kwargs.get("resource_scope") == "document:7"
            and self.host.allowed
        )
        return {"allowed": allowed, "reason": "verified" if allowed else "denied"}


class _JWTTrustedHost:
    def __init__(self, verifier):
        self.verifier = verifier
        self.allowed = True

    def authenticate(self, session):
        return self.verifier(session)

    def resolve_entity_context(self, principal, entity_id, key_id, capability_id):
        if (principal.get("workspace_id"), entity_id, key_id, capability_id) != (
            "workspace-a", "entity-a", "key-a", "capability.read"
        ):
            return None
        return {"artifact_digest": hashlib.sha256(b"artifact-v1").hexdigest()}

    def load_active_grants(self, principal, entity_id):
        return [{"grant_id": "grant-1"}] if self.allowed else []

    def build_action_gate(self, *, authenticate=None):
        return _Gate(authenticate or self.authenticate, self)


class _HostServices:
    def __init__(self, approvals):
        self.approvals = approvals

    def build_worker(self):
        return object()


class ExecutionHTTPJWTBindingTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.key = b"j" * 32
        self.verifier = HS256SessionVerifier(
            self.key, issuer="https://identity.example",
            audience="xparallel-api", clock=lambda: self.now,
            leeway_seconds=0,
        )
        self.host = _JWTTrustedHost(self.verifier)
        self.control = TrustedExecutionControlPlane(
            trusted_host=self.host,
            authorize_approval=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_cancel=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_executor=lambda principal, intent: principal["subject"] == "worker:1",
            db_path=":memory:",
        )
        self.api = ExecutionHTTPAPI(
            control_plane=self.control,
            host_services=_HostServices(self.control.approvals),
        )
        self.owner_token = self._signed("owner:1", "owner")
        self.admin_token = self._signed("admin:1", "admin")
        self.owner_claims = self.verifier(self.owner_token)
        self.admin_claims = self.verifier(self.admin_token)

    def tearDown(self):
        self.control.close()

    def _signed(self, subject, role):
        return _token({
            "iss": "https://identity.example", "aud": "xparallel-api",
            "sub": subject, "workspace_id": "workspace-a", "role": role,
            "iat": self.now - 10, "nbf": self.now - 10, "exp": self.now + 300,
        }, self.key)

    def test_api_revalidates_original_jwt_at_registry_boundary(self):
        limits = {
            "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
            "pids": 32, "output_bytes": 100000,
        }
        body = {
            "entity_id": "entity-a", "key_id": "key-a",
            "capability_id": "capability.read", "action": "read",
            "resource_scope": "document:7",
            "payload_digest": hashlib.sha256(b"payload").hexdigest(),
            "artifact_digest": hashlib.sha256(b"artifact-v1").hexdigest(),
            "runner_image_digest": hashlib.sha256(b"runner").hexdigest(),
            "limits": limits,
        }
        requested = self.api.request_intent(
            self.owner_claims, body, session_token=self.owner_token
        )
        self.assertEqual(requested["intent"]["status"], "requested")
        approved = self.api.approve_intent(
            self.admin_claims,
            {"intent_id": requested["intent"]["intent_id"], "reason": "Independent approval"},
            session_token=self.admin_token,
        )
        self.assertEqual(approved["approval"]["intent"]["status"], "approved")
        self.assertTrue(approved["approval"]["one_time_ticket"])

    def test_tampered_token_is_rejected_by_registry_even_with_claims_argument(self):
        parts = self.owner_token.split(".")
        signature = ("A" if parts[2][0] != "A" else "B") + parts[2][1:]
        forged = ".".join((parts[0], parts[1], signature))
        body = {
            "entity_id": "entity-a", "key_id": "key-a",
            "capability_id": "capability.read", "action": "read",
            "resource_scope": "document:7",
            "payload_digest": hashlib.sha256(b"payload").hexdigest(),
            "artifact_digest": hashlib.sha256(b"artifact-v1").hexdigest(),
            "runner_image_digest": hashlib.sha256(b"runner").hexdigest(),
            "limits": {
                "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
                "pids": 32, "output_bytes": 100000,
            },
        }
        with self.assertRaises(PermissionError):
            self.api.request_intent(
                self.owner_claims, body, session_token=forged,
            )


if __name__ == "__main__":
    unittest.main()
