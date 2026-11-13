import hashlib
import tempfile
import unittest
from pathlib import Path

from xparallel.capability_verification import CapabilityVerificationLab
from xparallel.entity_governance import EntityGovernanceRegistry
from xparallel.verified_action_gate import VerifiedEntityActionGate


ARTIFACT = hashlib.sha256(b"approved-research-artifact").hexdigest()


class DriSecurityIntegrationTests(unittest.TestCase):
    """Composition test: governed grant + verification evidence + action gate.

    Every identity, authority and sandbox adapter below is an explicit test
    double. This proves module composition, not production authentication or
    sandbox isolation.
    """

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.sessions = {
            "owner": {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-a"},
            "approver": {"authenticated": True, "subject": "admin:1", "workspace_id": "ws-a"},
            "verifier": {"authenticated": True, "subject": "verifier:1", "workspace_id": "ws-a"},
            "outsider": {"authenticated": True, "subject": "other:1", "workspace_id": "ws-a"},
        }
        self.authorities = {
            ("admin:1", "entity-a", "approve"),
            ("admin:1", "entity-a", "revoke"),
        }
        self.context = {
            "owner_subject": "owner:1",
            "entity_status": "active",
            "key_status": "active",
            "capability_version": "1.0.0",
            "artifact_digest": ARTIFACT,
        }
        root = Path(self.temp.name)
        self.governance = EntityGovernanceRegistry(
            authenticate=lambda session: self.sessions.get(session, {"authenticated": False}),
            resolve_owner=lambda workspace, entity: (
                "owner:1" if (workspace, entity) == ("ws-a", "entity-a") else None
            ),
            authorize_governance=lambda principal, entity, operation: (
                principal["subject"], entity, operation
            ) in self.authorities,
            db_path=str(root / "governance.sqlite3"),
        )
        self.lab = CapabilityVerificationLab(
            authenticate=lambda session: self.sessions.get(session, {"authenticated": False}),
            authorize_verifier=lambda principal, entity, capability, operation: (
                principal["subject"] == "verifier:1" and operation == "run"
            ),
            resolve_test_plan=lambda plan_id, version, entity, capability: {
                "plan_id": plan_id, "version": version, "case_ids": ["scope.read"],
            },
            execute_tests=lambda entity, capability, version, digest, plan: {
                "cases": [{
                    "case_id": "scope.read", "status": "pass",
                    "evidence_ref": "test-evidence:scope-read",
                }],
            },
            db_path=str(root / "verification.sqlite3"),
        )
        self.gate = VerifiedEntityActionGate(
            authenticate=lambda session: self.sessions.get(session, {"authenticated": False}),
            resolve_entity_context=lambda principal, entity, key, capability: self.context,
            load_active_grants=lambda principal, entity: self.governance.active_grants(
                principal["workspace_id"], entity
            ),
            verification_lab=self.lab,
        )

    def tearDown(self):
        self.governance.close()
        self.lab.close()
        self.temp.cleanup()

    def request_grant(self):
        return self.governance.request_grant(
            "owner", entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read",
            resource_scope="source:document-7", ttl_seconds=3600,
        )

    def verify_artifact(self, status="pass"):
        if status != "pass":
            self.lab._execute = lambda *args: {"cases": [{
                "case_id": "scope.read", "status": status,
                "evidence_ref": "test-evidence:scope-read",
            }]}
        return self.lab.run(
            "verifier", entity_id="entity-a", capability_id="research.read",
            capability_version="1.0.0", artifact_digest=ARTIFACT,
            plan_id="trusted-plan", plan_version="1.0",
        )

    def authorize(self, session="owner"):
        return self.gate.authorize(
            session, entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read",
            resource_scope="source:document-7",
        )

    def test_governed_verified_exact_scope_chain_allows(self):
        request = self.request_grant()
        self.assertEqual(request["status"], "pending")
        self.assertFalse(self.authorize()["allowed"])
        approved = self.governance.approve("approver", request["grant_id"])
        self.assertEqual(approved["status"], "approved")
        self.verify_artifact()
        decision = self.authorize()
        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["grant_id"], approved["grant_id"])
        self.assertEqual(decision["capability_evidence"]["status"], "verified")

    def test_revoked_grant_denies_even_with_verified_artifact(self):
        request = self.request_grant()
        self.governance.approve("approver", request["grant_id"])
        self.verify_artifact()
        self.assertTrue(self.authorize()["allowed"])
        self.governance.revoke("approver", request["grant_id"], "test revocation")
        self.assertFalse(self.authorize()["allowed"])

    def test_failed_capability_evidence_denies_even_with_approved_grant(self):
        request = self.request_grant()
        self.governance.approve("approver", request["grant_id"])
        self.verify_artifact(status="fail")
        decision = self.authorize()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["capability_evidence"]["status"], "failed")

    def test_changed_artifact_digest_invalidates_evidence(self):
        request = self.request_grant()
        self.governance.approve("approver", request["grant_id"])
        self.verify_artifact()
        self.context["artifact_digest"] = hashlib.sha256(b"changed-artifact").hexdigest()
        decision = self.authorize()
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["capability_evidence"]["status"], "unverified")

    def test_unauthenticated_caller_is_denied(self):
        decision = self.authorize("unknown-session")
        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "caller_not_authenticated")


if __name__ == "__main__":
    unittest.main()
