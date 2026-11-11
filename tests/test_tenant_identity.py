import unittest
from unittest.mock import patch

from xparallel.tenant_identity import (
    IdentityError, issue_identity_token, verify_identity_token,
)


SECRET = "test-secret-that-is-at-least-thirty-two-bytes-long"


class TenantIdentityTests(unittest.TestCase):
    def test_round_trip_returns_trusted_tenant_claims(self):
        token = issue_identity_token(
            subject="user-1", workspace_id="workspace-a", role="operator",
            secret=SECRET, now=1000,
        )
        claims = verify_identity_token(token, secret=SECRET, now=1001)
        self.assertEqual(claims["actor"], "user-1")
        self.assertEqual(claims["workspace_id"], "workspace-a")
        self.assertEqual(claims["role"], "operator")

    def test_tampering_is_rejected(self):
        token = issue_identity_token(
            subject="user-1", workspace_id="workspace-a", role="viewer",
            secret=SECRET, now=1000,
        )
        parts = token.split(".")
        parts[1] = parts[1][:-1] + ("A" if parts[1][-1] != "A" else "B")
        with self.assertRaises(IdentityError):
            verify_identity_token(".".join(parts), secret=SECRET, now=1001)

    def test_expired_token_is_rejected(self):
        token = issue_identity_token(
            subject="user-1", workspace_id="workspace-a", role="viewer",
            secret=SECRET, now=1000, ttl_seconds=10,
        )
        with self.assertRaisesRegex(IdentityError, "expired"):
            verify_identity_token(token, secret=SECRET, now=1010)

    def test_weak_secret_and_invalid_role_are_rejected(self):
        with self.assertRaisesRegex(IdentityError, "not_configured"):
            issue_identity_token(
                subject="u", workspace_id="w", role="owner", secret="weak", now=1,
            )
        with self.assertRaisesRegex(IdentityError, "invalid_identity_role"):
            issue_identity_token(
                subject="u", workspace_id="w", role="root",
                secret=SECRET, now=1,
            )

    def test_configured_issuer_and_audience_are_enforced(self):
        token = issue_identity_token(
            subject="nexai-user", workspace_id="nexai-workspace", role="owner",
            secret=SECRET, now=1000, issuer="nexai-platform",
            audience="axaliai-enterprise",
        )
        with patch.dict("os.environ", {
            "XP_IDENTITY_ISSUER": "nexai-platform",
            "XP_IDENTITY_AUDIENCE": "axaliai-enterprise",
        }):
            claims = verify_identity_token(token, secret=SECRET, now=1001)
            self.assertEqual(claims["actor"], "nexai-user")
        with patch.dict("os.environ", {"XP_IDENTITY_ISSUER": "other-issuer"}):
            with self.assertRaisesRegex(IdentityError, "issuer"):
                verify_identity_token(token, secret=SECRET, now=1001)
        with patch.dict("os.environ", {"XP_IDENTITY_AUDIENCE": "other-audience"}):
            with self.assertRaisesRegex(IdentityError, "audience"):
                verify_identity_token(token, secret=SECRET, now=1001)

    def test_token_lifetime_is_bounded(self):
        with self.assertRaisesRegex(IdentityError, "invalid_identity_ttl"):
            issue_identity_token(
                subject="u", workspace_id="w", role="owner",
                secret=SECRET, ttl_seconds=7200, now=1,
            )


if __name__ == "__main__":
    unittest.main()
