import unittest

from xparallel.trusted_runtime import TrustedRuntimeContext


class TrustedRuntimeContextTests(unittest.TestCase):
    def setUp(self):
        self.sessions = {
            "valid": {
                "authenticated": True,
                "subject": "user:alice",
                "workspace_id": "workspace-a",
            },
            "anonymous": {"authenticated": False},
            "missing_subject": {
                "authenticated": True,
                "workspace_id": "workspace-a",
            },
            "bad_workspace": {
                "authenticated": True,
                "subject": "user:alice",
                "workspace_id": "../other",
            },
        }
        self.context = TrustedRuntimeContext(
            lambda session: self.sessions.get(session, {"authenticated": False})
        )

    def test_principal_comes_from_authenticated_host_claims(self):
        principal = self.context.resolve("valid")
        self.assertEqual(principal["subject"], "user:alice")
        self.assertEqual(principal["workspace_id"], "workspace-a")
        self.assertEqual(principal["actor"], "user:alice")

    def test_matching_requested_workspace_is_only_a_consistency_check(self):
        principal = self.context.resolve("valid", requested_workspace="workspace-a")
        self.assertEqual(principal["workspace_id"], "workspace-a")

    def test_caller_cannot_select_another_workspace(self):
        with self.assertRaisesRegex(PermissionError, "workspace_claim_mismatch"):
            self.context.resolve("valid", requested_workspace="workspace-b")

    def test_unauthenticated_or_unknown_session_fails_closed(self):
        for session in ("anonymous", "unknown"):
            with self.subTest(session=session):
                with self.assertRaises(PermissionError):
                    self.context.resolve(session)

    def test_incomplete_or_malformed_trusted_claims_fail_closed(self):
        for session in ("missing_subject", "bad_workspace"):
            with self.subTest(session=session):
                with self.assertRaises(PermissionError):
                    self.context.resolve(session)

    def test_authenticator_failure_fails_closed(self):
        def broken(_session):
            raise RuntimeError("identity provider unavailable")

        with self.assertRaisesRegex(PermissionError, "trusted_authentication_failed"):
            TrustedRuntimeContext(broken).resolve("session")


if __name__ == "__main__":
    unittest.main()
