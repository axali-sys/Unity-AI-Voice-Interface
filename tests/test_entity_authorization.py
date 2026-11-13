import unittest
from datetime import datetime, timedelta, timezone

from xparallel.entity_authorization import authorize_entity_action


NOW = datetime(2026, 11, 13, 12, 0, tzinfo=timezone.utc)


def identity(**changes):
    value = {
        "authenticated": True,
        "workspace_id": "workspace-a",
        "subject": "user:123",
        "owner_subject": "user:123",
        "entity_id": "xp:entity:agent-a",
        "entity_status": "active",
        "key_id": "key-1",
        "key_status": "active",
        "capability_id": "research.summarize",
        "capability_status": "verified",
    }
    value.update(changes)
    return value


def grant(**changes):
    value = {
        "grant_id": "grant-1",
        "workspace_id": "workspace-a",
        "subject": "user:123",
        "entity_id": "xp:entity:agent-a",
        "key_id": "key-1",
        "capability_id": "research.summarize",
        "action": "read",
        "resource_scope": "public-source:article-1",
        "status": "approved",
        "expires_at": (NOW + timedelta(minutes=10)).isoformat(),
    }
    value.update(changes)
    return value


class EntityAuthorizationTests(unittest.TestCase):
    def decide(self, who=None, grants=None, **kwargs):
        return authorize_entity_action(
            who or identity(), grants if grants is not None else [grant()],
            action=kwargs.get("action", "read"),
            resource_scope=kwargs.get("resource_scope", "public-source:article-1"),
            now=NOW,
        )

    def test_exact_approved_grant_allows_action(self):
        result = self.decide()
        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "explicit_grant_matched")

    def test_missing_authentication_denied(self):
        self.assertEqual(self.decide(identity(authenticated=False))["reason"], "caller_not_authenticated")

    def test_owner_subject_mismatch_denied(self):
        self.assertEqual(self.decide(identity(subject="user:attacker"))["reason"], "owner_subject_mismatch")

    def test_inactive_entity_denied(self):
        self.assertEqual(self.decide(identity(entity_status="pending"))["reason"], "entity_not_active")

    def test_revoked_key_denied(self):
        self.assertEqual(self.decide(identity(key_status="revoked"))["reason"], "signing_key_not_active")

    def test_declared_but_unverified_capability_denied(self):
        self.assertEqual(self.decide(identity(capability_status="declared"))["reason"], "capability_not_verified")

    def test_wrong_workspace_or_scope_denied(self):
        self.assertFalse(self.decide(grants=[grant(workspace_id="workspace-b")])["allowed"])
        self.assertFalse(self.decide(resource_scope="public-source:article-1/other")["allowed"])

    def test_wrong_key_or_action_denied(self):
        self.assertFalse(self.decide(grants=[grant(key_id="key-old")])["allowed"])
        self.assertFalse(self.decide(action="delete")["allowed"])

    def test_expired_or_unapproved_grant_denied(self):
        expired = grant(expires_at=(NOW - timedelta(seconds=1)).isoformat())
        pending = grant(status="pending")
        self.assertFalse(self.decide(grants=[expired])["allowed"])
        self.assertFalse(self.decide(grants=[pending])["allowed"])

    def test_no_grant_is_deny_by_default(self):
        self.assertEqual(self.decide(grants=[])["reason"], "no_matching_unexpired_grant")


if __name__ == "__main__":
    unittest.main()
