import unittest

from xparallel.http_identity import (
    IdentityBindingError,
    bearer_token,
    bind_request_identity,
)


class HttpIdentityBindingTests(unittest.TestCase):
    def setUp(self):
        self.claims = {
            "authenticated": True,
            "subject": "user:alice",
            "workspace_id": "workspace-a",
            "role": "operator",
        }

    def test_bearer_header_is_parsed_strictly(self):
        self.assertEqual(bearer_token("Bearer abc.def"), "abc.def")
        self.assertEqual(bearer_token("bearer token"), "token")
        for value in (None, "", "Basic abc", "Bearer ", "Bearer a b"):
            with self.subTest(value=value):
                self.assertIsNone(bearer_token(value))

    def test_workspace_and_actor_are_derived_from_verified_claims(self):
        result = bind_request_identity({"query": "hello"}, self.claims)
        self.assertEqual(result["workspace_id"], "workspace-a")
        self.assertEqual(result["actor"], "user:alice")
        self.assertEqual(result["query"], "hello")

    def test_matching_identity_fields_are_allowed(self):
        result = bind_request_identity({
            "workspace_id": "workspace-a", "actor": "user:alice"
        }, self.claims)
        self.assertEqual(result["workspace_id"], "workspace-a")

    def test_query_string_identity_is_checked_without_trusting_parameter_lists(self):
        result = bind_request_identity({
            "workspace_id": ["workspace-a"], "limit": ["10"]
        }, self.claims)
        self.assertEqual(result["workspace_id"], "workspace-a")
        with self.assertRaisesRegex(IdentityBindingError, "workspace_claim_mismatch"):
            bind_request_identity({"workspace_id": ["workspace-b"]}, self.claims)
        with self.assertRaisesRegex(IdentityBindingError, "ambiguous_identity_parameter"):
            bind_request_identity({"workspace_id": ["workspace-a", "workspace-b"]}, self.claims)

    def test_cross_workspace_and_actor_spoofing_are_rejected(self):
        with self.assertRaisesRegex(IdentityBindingError, "workspace_claim_mismatch"):
            bind_request_identity({"workspace_id": "workspace-b"}, self.claims)
        with self.assertRaisesRegex(IdentityBindingError, "actor_claim_mismatch"):
            bind_request_identity({"actor": "user:mallory"}, self.claims)

    def test_invalid_trusted_role_fails_closed(self):
        with self.assertRaisesRegex(IdentityBindingError, "trusted_role_invalid"):
            bind_request_identity({}, {**self.claims, "role": "superuser"})

    def test_missing_trusted_identity_fails_closed(self):
        with self.assertRaises(IdentityBindingError):
            bind_request_identity({}, {"workspace_id": "workspace-a"})


if __name__ == "__main__":
    unittest.main()
