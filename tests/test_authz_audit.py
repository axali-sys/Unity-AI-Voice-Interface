import unittest

from xparallel.authz import ACTIONS, ROLES, authorize
from xparallel.audit import audit_event


class AuthorizationPolicyTests(unittest.TestCase):
    def test_role_boundaries(self):
        self.assertTrue(authorize("viewer", "read"))
        self.assertTrue(authorize("viewer", "search"))
        self.assertFalse(authorize("viewer", "create_solution"))
        self.assertTrue(authorize("operator", "create_solution"))
        self.assertFalse(authorize("operator", "verify"))
        self.assertTrue(authorize("admin", "verify"))
        self.assertFalse(authorize("admin", "approve_deployment"))
        self.assertTrue(authorize("owner", "approve_deployment"))
        self.assertTrue(authorize("admin", "billing"))

    def test_unknown_roles_and_actions_fail_closed(self):
        self.assertFalse(authorize("superuser", "read"))
        self.assertFalse(authorize("viewer", "delete_everything"))

    def test_non_string_inputs_fail_closed_without_raising(self):
        for role, action in (
            (None, "read"),
            ([], "read"),
            ("viewer", None),
            ("viewer", ["read"]),
            ({}, {}),
        ):
            with self.subTest(role=role, action=action):
                self.assertFalse(authorize(role, action))

    def test_policy_tables_cannot_be_mutated_at_runtime(self):
        with self.assertRaises(TypeError):
            ROLES["viewer"] = 99
        with self.assertRaises(TypeError):
            ACTIONS["delete_everything"] = 0
        self.assertFalse(authorize("viewer", "approve_deployment"))

    def test_audit_is_tamper_evident(self):
        event = audit_event("verification", "acme", "owner", {"node_id": "x"})
        self.assertEqual(len(event["event_fingerprint"]), 64)


if __name__ == "__main__":
    unittest.main()
