import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from xparallel.entity_governance import EntityGovernanceRegistry
from xparallel.entity_authorization import authorize_entity_action


class GovernanceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.sessions = {
            "owner": {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-a"},
            "approver": {"authenticated": True, "subject": "admin:1", "workspace_id": "ws-a"},
            "outsider": {"authenticated": True, "subject": "other:1", "workspace_id": "ws-a"},
            "other-ws": {"authenticated": True, "subject": "admin:1", "workspace_id": "ws-b"},
            "anonymous": {"authenticated": False},
        }
        self.owners = {("ws-a", "entity-a"): "owner:1"}
        self.authorized = {("admin:1", "entity-a", "approve"),
                           ("admin:1", "entity-a", "suspend"),
                           ("admin:1", "entity-a", "reinstate"),
                           ("admin:1", "entity-a", "revoke"),
                           ("admin:1", "entity-a", "audit")}
        def authenticate(session):
            return self.sessions.get(session, {"authenticated": False})
        def resolve_owner(workspace, entity):
            return self.owners.get((workspace, entity))
        def authorize(principal, entity, operation):
            return (principal["subject"], entity, operation) in self.authorized
        self.registry = EntityGovernanceRegistry(
            authenticate=authenticate, resolve_owner=resolve_owner,
            authorize_governance=authorize,
            db_path=str(Path(self.temp.name) / "governance.sqlite3")
        )

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def request(self):
        return self.registry.request_grant(
            "owner", entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read",
            resource_scope="source:document-7", ttl_seconds=3600
        )

    def approved(self):
        req = self.request()
        return self.registry.approve("approver", req["grant_id"])

    def test_request_starts_pending_and_is_not_active(self):
        req = self.request()
        self.assertEqual(req["status"], "pending")
        self.assertEqual(self.registry.active_grants("ws-a", "entity-a"), [])

    def test_owner_can_request_but_non_owner_cannot(self):
        with self.assertRaisesRegex(PermissionError, "entity_owner_mismatch"):
            self.registry.request_grant(
                "outsider", entity_id="entity-a", key_id="key-a",
                capability_id="research.read", action="read",
                resource_scope="source:document-7"
            )

    def test_unauthenticated_request_rejected(self):
        with self.assertRaisesRegex(PermissionError, "caller_not_authenticated"):
            self.registry.request_grant(
                "anonymous", entity_id="entity-a", key_id="key-a",
                capability_id="research.read", action="read",
                resource_scope="source:document-7"
            )

    def test_requester_cannot_approve_own_grant(self):
        req = self.request()
        with self.assertRaisesRegex(PermissionError, "requester_cannot_approve_own_grant"):
            self.registry.approve("owner", req["grant_id"])

    def test_approval_requires_governance_authority(self):
        req = self.request()
        with self.assertRaisesRegex(PermissionError, "governance_permission_denied"):
            self.registry.approve("outsider", req["grant_id"])

    def test_approved_grant_flows_into_existing_authorization_policy(self):
        approved = self.approved()
        grants = self.registry.active_grants("ws-a", "entity-a")
        identity = {
            "authenticated": True, "workspace_id": "ws-a", "subject": "owner:1",
            "owner_subject": "owner:1", "entity_id": "entity-a",
            "entity_status": "active", "key_id": "key-a", "key_status": "active",
            "capability_id": "research.read", "capability_status": "verified",
        }
        decision = authorize_entity_action(
            identity, grants, action="read", resource_scope="source:document-7"
        )
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["grant_id"], approved["grant_id"])

    def test_suspended_grant_is_not_active_and_can_be_reinstated(self):
        approved = self.approved()
        self.registry.suspend("approver", approved["grant_id"], "temporary review")
        self.assertEqual(self.registry.active_grants("ws-a", "entity-a"), [])
        restored = self.registry.reinstate("approver", approved["grant_id"], "review passed")
        self.assertEqual(restored["status"], "approved")
        self.assertEqual(len(self.registry.active_grants("ws-a", "entity-a")), 1)

    def test_revoked_grant_cannot_be_reinstated(self):
        approved = self.approved()
        self.registry.revoke("approver", approved["grant_id"], "owner requested revocation")
        self.assertEqual(self.registry.active_grants("ws-a", "entity-a"), [])
        with self.assertRaisesRegex(ValueError, "grant_not_suspended"):
            self.registry.reinstate("approver", approved["grant_id"], "try again")

    def test_expired_approved_grant_is_not_returned(self):
        self.approved()
        future = datetime.now(timezone.utc) + timedelta(days=2)
        self.assertEqual(
            self.registry.active_grants("ws-a", "entity-a", now=future), []
        )

    def test_ttl_bounds_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "grant_ttl_out_of_range"):
            self.registry.request_grant(
                "owner", entity_id="entity-a", key_id="key-a",
                capability_id="research.read", action="read",
                resource_scope="source:document-7", ttl_seconds=1
            )

    def test_workspace_isolation(self):
        approved = self.approved()
        self.assertIsNone(self.registry.get("other-ws", approved["grant_id"]))
        self.assertEqual(self.registry.active_grants("ws-b", "entity-a"), [])

    def test_exact_scope_and_no_wildcards(self):
        with self.assertRaisesRegex(ValueError, "wildcard_or_multiline_scope_not_allowed"):
            self.registry.request_grant(
                "owner", entity_id="entity-a", key_id="key-a",
                capability_id="research.read", action="read",
                resource_scope="source:*"
            )

    def test_audit_history_is_append_only_and_scoped(self):
        approved = self.approved()
        self.registry.suspend("approver", approved["grant_id"], "review")
        events = self.registry.events("owner", approved["grant_id"])
        self.assertEqual([event["event_type"] for event in events],
                         ["requested", "approved", "suspended"])
        with self.assertRaisesRegex(PermissionError, "grant_audit_forbidden"):
            self.registry.events("outsider", approved["grant_id"])

    def test_governance_adapters_are_mandatory(self):
        with self.assertRaises(TypeError):
            EntityGovernanceRegistry(authenticate=lambda s: {}, resolve_owner=None,
                                     authorize_governance=lambda p, e, o: True)


if __name__ == "__main__":
    unittest.main()
