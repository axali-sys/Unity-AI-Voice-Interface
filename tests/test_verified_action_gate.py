import hashlib
import tempfile
import unittest
from pathlib import Path

from xparallel.capability_verification import CapabilityVerificationLab
from xparallel.verified_action_gate import VerifiedEntityActionGate


ARTIFACT = hashlib.sha256(b"immutable-artifact").hexdigest()


class VerifiedActionGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.principal = {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-a"}
        self.context = {
            "owner_subject": "owner:1", "entity_status": "active", "key_status": "active",
            "capability_version": "1.0.0", "artifact_digest": ARTIFACT,
        }
        self.grants = [{
            "grant_id": "grant-1", "workspace_id": "ws-a", "entity_id": "entity-a",
            "subject": "owner:1", "key_id": "key-a", "capability_id": "research.read",
            "action": "read", "resource_scope": "doc:7", "status": "approved",
            "expires_at": "2099-01-01T00:00:00+00:00",
        }]
        self.allowed_ops = {"run", "read", "audit", "suspended", "revoked"}
        self.lab = CapabilityVerificationLab(
            authenticate=lambda s: {"authenticated": True, "subject": "verifier", "workspace_id": "ws-a"},
            authorize_verifier=lambda p, e, c, op: op in self.allowed_ops,
            resolve_test_plan=lambda pid, ver, e, c: {
                "plan_id": pid, "version": ver, "case_ids": ["case.one"]
            },
            execute_tests=lambda e, c, v, d, p: {"cases": [
                {"case_id": "case.one", "status": "pass", "evidence_ref": "evidence:one"}
            ]},
            db_path=str(Path(self.temp.name) / "lab.sqlite3"),
        )
        self.gate = VerifiedEntityActionGate(
            authenticate=lambda s: self.principal if s == "valid" else {"authenticated": False},
            resolve_entity_context=lambda p, e, k, c: self.context,
            load_active_grants=lambda p, e: self.grants,
            verification_lab=self.lab,
        )

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def verify(self):
        return self.lab.run(
            "verifier", entity_id="entity-a", capability_id="research.read",
            capability_version="1.0.0", artifact_digest=ARTIFACT,
            plan_id="plan.standard", plan_version="1.0",
        )

    def authorize(self, session="valid"):
        return self.gate.authorize(
            session, entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read", resource_scope="doc:7",
        )

    def test_full_identity_evidence_and_grant_chain_allows(self):
        self.verify()
        result = self.authorize()
        self.assertTrue(result["allowed"])
        self.assertEqual(result["reason"], "explicit_grant_matched")
        self.assertEqual(result["capability_evidence"]["status"], "verified")

    def test_declared_or_unverified_capability_is_denied(self):
        result = self.authorize()
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "capability_not_verified")
        self.assertEqual(result["capability_evidence"]["status"], "unverified")

    def test_failed_verification_denied_even_with_grant(self):
        self.lab._execute = lambda *a: {"cases": [
            {"case_id": "case.one", "status": "fail", "evidence_ref": "evidence:fail"}
        ]}
        self.verify()
        self.assertFalse(self.authorize()["allowed"])

    def test_suspended_and_revoked_capability_denied(self):
        self.verify()
        self.lab.set_control(
            "verifier", entity_id="entity-a", capability_id="research.read",
            capability_version="1.0.0", status="suspended", reason="review",
        )
        self.assertEqual(self.authorize()["capability_evidence"]["status"], "suspended")
        self.assertFalse(self.authorize()["allowed"])

    def test_artifact_change_invalidates_previously_passed_evidence(self):
        self.verify()
        self.context["artifact_digest"] = hashlib.sha256(b"new artifact").hexdigest()
        result = self.authorize()
        self.assertFalse(result["allowed"])
        self.assertEqual(result["capability_evidence"]["reason"], "artifact_digest_changed")

    def test_owner_or_key_or_entity_mismatch_denied(self):
        self.verify()
        self.context["owner_subject"] = "other-owner"
        self.assertEqual(self.authorize()["reason"], "owner_subject_mismatch")
        self.context["owner_subject"] = "owner:1"
        self.context["key_status"] = "revoked"
        self.assertEqual(self.authorize()["reason"], "signing_key_not_active")
        self.context["key_status"] = "active"
        self.context["entity_status"] = "suspended"
        self.assertEqual(self.authorize()["reason"], "entity_not_active")

    def test_wrong_grant_scope_denied(self):
        self.verify()
        result = self.gate.authorize(
            "valid", entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read", resource_scope="doc:8",
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reason"], "no_matching_unexpired_grant")

    def test_authentication_and_dependency_failures_deny(self):
        self.assertEqual(self.authorize("invalid")["reason"], "caller_not_authenticated")
        broken = VerifiedEntityActionGate(
            authenticate=lambda s: self.principal,
            resolve_entity_context=lambda *a: (_ for _ in ()).throw(RuntimeError("offline")),
            load_active_grants=lambda *a: self.grants,
            verification_lab=self.lab,
        )
        self.assertFalse(broken.authorize(
            "valid", entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read", resource_scope="doc:7",
        )["allowed"])

    def test_unavailable_grant_repository_denies(self):
        broken = VerifiedEntityActionGate(
            authenticate=lambda s: self.principal,
            resolve_entity_context=lambda *a: self.context,
            load_active_grants=lambda *a: None,
            verification_lab=self.lab,
        )
        self.assertEqual(broken.authorize(
            "valid", entity_id="entity-a", key_id="key-a",
            capability_id="research.read", action="read", resource_scope="doc:7",
        )["reason"], "trusted_grant_repository_unavailable")


if __name__ == "__main__":
    unittest.main()
