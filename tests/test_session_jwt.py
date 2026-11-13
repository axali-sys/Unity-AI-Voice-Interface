import base64
import hashlib
import hmac
import json
import unittest

from xparallel.session_jwt import HS256SessionVerifier


def segment(value):
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def token(claims, key=b"x" * 32, header=None):
    head = segment(header or {"alg": "HS256", "typ": "JWT"})
    body = segment(claims)
    message = f"{head}.{body}".encode()
    signature = hmac.new(key, message, hashlib.sha256).digest()
    return f"{head}.{body}." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


class HS256SessionVerifierTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.key = b"x" * 32
        self.verifier = HS256SessionVerifier(
            self.key, issuer="https://identity.example",
            audience="xparallel-api", clock=lambda: self.now, leeway_seconds=0,
        )
        self.claims = {
            "iss": "https://identity.example", "aud": "xparallel-api",
            "sub": "user:alice", "workspace_id": "workspace-a",
            "iat": self.now - 10, "nbf": self.now - 10, "exp": self.now + 300,
        }

    def test_valid_signed_token_returns_trusted_claims(self):
        claims = self.verifier(token(self.claims, self.key))
        self.assertEqual(claims, {
            "authenticated": True, "subject": "user:alice",
            "workspace_id": "workspace-a",
        })

    def test_tampered_signature_is_rejected(self):
        value = token(self.claims, self.key)
        changed = value[:-1] + ("A" if value[-1] != "A" else "B")
        with self.assertRaises(PermissionError):
            self.verifier(changed)

    def test_expired_token_is_rejected(self):
        claims = {**self.claims, "exp": self.now - 1}
        with self.assertRaisesRegex(PermissionError, "expired"):
            self.verifier(token(claims, self.key))

    def test_not_yet_valid_token_is_rejected(self):
        claims = {**self.claims, "nbf": self.now + 10}
        with self.assertRaisesRegex(PermissionError, "not_yet_valid"):
            self.verifier(token(claims, self.key))

    def test_wrong_issuer_or_audience_is_rejected(self):
        for claims in (
            {**self.claims, "iss": "https://attacker.invalid"},
            {**self.claims, "aud": "another-api"},
        ):
            with self.subTest(claims=claims):
                with self.assertRaises(PermissionError):
                    self.verifier(token(claims, self.key))

    def test_wrong_algorithm_and_bad_workspace_are_rejected(self):
        with self.assertRaisesRegex(PermissionError, "algorithm"):
            self.verifier(token(self.claims, self.key, {"alg": "none"}))
        claims = {**self.claims, "workspace_id": "../other"}
        with self.assertRaisesRegex(PermissionError, "workspace"):
            self.verifier(token(claims, self.key))

    def test_missing_expiry_and_short_secret_are_rejected(self):
        claims = dict(self.claims)
        del claims["exp"]
        with self.assertRaisesRegex(PermissionError, "expiry"):
            self.verifier(token(claims, self.key))
        with self.assertRaisesRegex(ValueError, "32_bytes"):
            HS256SessionVerifier(b"short", issuer="issuer", audience="audience")

    def test_malformed_tokens_fail_closed(self):
        for value in ("", "one.two", "a.b.c", None, "x" * 9000):
            with self.subTest(value=value):
                with self.assertRaises((PermissionError, ValueError)):
                    self.verifier(value)


if __name__ == "__main__":
    unittest.main()
