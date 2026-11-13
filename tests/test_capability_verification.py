import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from xparallel.capability_verification import CapabilityVerificationLab


ARTIFACT = hashlib.sha256(b"example immutable build").hexdigest()


class CapabilityVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.sessions = {
            "verifier": {"authenticated": True, "subject": "verifier:1", "workspace_id": "ws-a"},
            "unauthorized": {"authenticated": True, "subject": "user:2", "workspace_id": "ws-a"},
            "other-ws": {"authenticated": True, "subject": "verifier:1", "workspace_id": "ws-b"},
            "anonymous": {"authenticated": False},
        }
        self.allowed = {("verifier:1", "entity-a", "capability-a", op)
                        for op in ("run", "suspended", "revoked", "read", "audit")}
        self.outcome = "pass"
        self.case_ids = ["case.input", "case.output"]
        def authenticate(session):
            return self.sessions.get(session, {"authenticated": False})
        def authorize(principal, entity, capability, operation):
            return (principal["subject"], entity, capability, operation) in self.allowed
        def resolve_plan(plan_id, version, entity, capability):
            return {"plan_id": plan_id, "version": version, "case_ids": list(self.case_ids)}
        def execute(entity, capability, version, digest, plan):
            return {"cases": [
                {"case_id": case_id, "status": self.outcome, "evidence_ref": "local-evidence:" + case_id}
                for case_id in plan["case_ids"]
            ]}
        self.lab = CapabilityVerificationLab(
            authenticate=authenticate, authorize_verifier=authorize,
            resolve_test_plan=resolve_plan, execute_tests=execute,
            db_path=str(Path(self.temp.name) / "verification.sqlite3")
        )

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def run_test(self, **kwargs):
        args = {
            "entity_id": "entity-a", "capability_id": "capability-a",
            "capability_version": "1.0.0", "artifact_digest": ARTIFACT,
            "plan_id": "plan.standard", "plan_version": "1.0",
            "expires_in_seconds": 3600,
        }
        args.update(kwargs)
        return self.lab.run("verifier", **args)

    def test_all_passed_cases_create_verified_evidence_for_exact_artifact(self):
        run = self.run_test()
        status = self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", ARTIFACT)
        self.assertEqual(run["outcome"], "passed")
        self.assertEqual(status["status"], "verified")
        self.assertEqual(status["run_id"], run["run_id"])

    def test_failed_case_does_not_verify_capability(self):
        self.outcome = "fail"
        run = self.run_test()
        status = self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", ARTIFACT)
        self.assertEqual(run["outcome"], "failed")
        self.assertEqual(status["status"], "failed")

    def test_blocked_case_is_inconclusive_not_verified(self):
        self.outcome = "blocked"
        self.assertEqual(self.run_test()["outcome"], "inconclusive")
        self.assertEqual(self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", ARTIFACT)["status"], "inconclusive")

    def test_untrusted_caller_cannot_run_tests(self):
        with self.assertRaisesRegex(PermissionError, "caller_not_authenticated"):
            self.lab.run("anonymous", entity_id="entity-a", capability_id="capability-a",
                         capability_version="1.0.0", artifact_digest=ARTIFACT,
                         plan_id="plan.standard", plan_version="1.0")

    def test_unauthorized_verifier_is_denied(self):
        self.sessions["verifier"] = self.sessions["unauthorized"]
        with self.assertRaisesRegex(PermissionError, "capability_verifier_permission_denied"):
            self.run_test()

    def test_invalid_artifact_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "artifact_digest_must_be_sha256"):
            self.run_test(artifact_digest="not-a-digest")

    def test_untrusted_or_mismatched_test_plan_rejected(self):
        self.lab._resolve_plan = lambda *args: {"plan_id": "attacker-plan", "version": "1.0", "case_ids": ["case.input"]}
        with self.assertRaisesRegex(ValueError, "trusted_test_plan_mismatch"):
            self.run_test()

    def test_incomplete_or_duplicate_sandbox_results_rejected(self):
        self.lab._execute = lambda *args: {"cases": [{"case_id": "case.input", "status": "pass", "evidence_ref": "e1"}]}
        with self.assertRaisesRegex(ValueError, "incomplete_test_case_results"):
            self.run_test()
        self.lab._execute = lambda *args: {"cases": [
            {"case_id": "case.input", "status": "pass", "evidence_ref": "e1"},
            {"case_id": "case.input", "status": "pass", "evidence_ref": "e2"},
        ]}
        with self.assertRaisesRegex(ValueError, "unexpected_or_duplicate_test_case"):
            self.run_test()

    def test_expired_verification_is_not_verified(self):
        run = self.run_test(expires_in_seconds=60)
        future = datetime.now(timezone.utc) + timedelta(minutes=2)
        status = self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", ARTIFACT, now=future)
        self.assertEqual(status["status"], "expired")
        self.assertEqual(status["run_id"], run["run_id"])

    def test_artifact_change_invalidates_verification(self):
        self.run_test()
        other = hashlib.sha256(b"different build").hexdigest()
        status = self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", other)
        self.assertEqual(status["status"], "unverified")
        self.assertEqual(status["reason"], "artifact_digest_changed")

    def test_workspace_isolation(self):
        self.run_test()
        self.assertEqual(self.lab.status("ws-b", "entity-a", "capability-a", "1.0.0", ARTIFACT)["status"], "unverified")
        self.assertIsNone(self.lab.get_run("other-ws", "vrun:not-a-real-run"))

    def test_suspension_and_revocation_override_passed_runs(self):
        self.run_test()
        self.lab.set_control("verifier", entity_id="entity-a", capability_id="capability-a",
                             capability_version="1.0.0", status="suspended", reason="review required")
        self.assertEqual(self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", ARTIFACT)["status"], "suspended")
        self.lab.set_control("verifier", entity_id="entity-a", capability_id="capability-a",
                             capability_version="1.0.0", status="revoked", reason="unsafe behavior")
        self.assertEqual(self.lab.status("ws-a", "entity-a", "capability-a", "1.0.0", ARTIFACT)["status"], "revoked")
        with self.assertRaisesRegex(ValueError, "capability_version_already_revoked"):
            self.lab.set_control("verifier", entity_id="entity-a", capability_id="capability-a",
                                 capability_version="1.0.0", status="suspended", reason="again")

    def test_revoked_version_cannot_be_reverified(self):
        self.lab.set_control("verifier", entity_id="entity-a", capability_id="capability-a",
                             capability_version="1.0.0", status="revoked", reason="withdrawn")
        with self.assertRaisesRegex(PermissionError, "capability_version_revoked"):
            self.run_test()

    def test_verification_audit_is_recorded_and_scoped(self):
        self.run_test()
        events = self.lab.events("verifier", "entity-a", "capability-a")
        self.assertEqual(events[0]["event_type"], "verification_passed")
        with self.assertRaisesRegex(PermissionError, "capability_verifier_permission_denied"):
            self.lab.events("unauthorized", "entity-a", "capability-a")

    def test_expiry_bounds_and_missing_evidence_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "verification_expiry_out_of_range"):
            self.run_test(expires_in_seconds=1)
        self.lab._execute = lambda *args: {"cases": [
            {"case_id": "case.input", "status": "pass", "evidence_ref": "e1"},
            {"case_id": "case.output", "status": "pass", "evidence_ref": ""},
        ]}
        with self.assertRaisesRegex(ValueError, "test_case_evidence_required"):
            self.run_test()

    def test_all_trusted_adapters_are_mandatory(self):
        with self.assertRaises(TypeError):
            CapabilityVerificationLab(authenticate=lambda s: {}, authorize_verifier=None,
                                      resolve_test_plan=lambda *a: {}, execute_tests=lambda *a: {})


if __name__ == "__main__":
    unittest.main()
