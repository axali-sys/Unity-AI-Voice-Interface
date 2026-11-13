import base64
import hashlib
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from xparallel.execution_approval import ExecutionApprovalRegistry
from xparallel.execution_receipts import ExecutionReceiptLedger

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
            "worker": {"authenticated": True, "subject": "worker:1", "workspace_id": "ws-a"},
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


    def test_verified_approval_worker_checkpoint_and_signed_receipt_chain(self):
        request = self.request_grant()
        approved_grant = self.governance.approve("approver", request["grant_id"])
        self.verify_artifact()
        decision = self.authorize()
        self.assertTrue(decision["allowed"])
        self.assertTrue(decision["capability_evidence"]["run_id"])
        limits = {
            "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
            "pids": 32, "output_bytes": 100000,
        }
        def validate_current(principal, intent, stage):
            result = self.authorize("owner")
            return bool(result["allowed"] and intent["artifact_digest"] == ARTIFACT
                        and intent["entity_id"] == "entity-a"
                        and intent["capability_id"] == "research.read")
        approvals = ExecutionApprovalRegistry(
            authenticate=lambda session: self.sessions.get(session, {"authenticated": False}),
            authorize_request=lambda principal, intent: (
                principal["subject"] == "owner:1" and bool(self.authorize("owner")["allowed"])
            ),
            authorize_approval=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_cancel=lambda principal, intent: principal["subject"] in {"owner:1", "admin:1"},
            authorize_executor=lambda principal, intent: principal["subject"] == "worker:1",
            validate_current_state=validate_current,
            db_path=str(Path(self.temp.name) / "execution-approvals.sqlite3"),
        )
        signing_key = Ed25519PrivateKey.generate()
        ledger = None
        try:
            intent = approvals.request_intent(
                "owner", entity_id="entity-a", key_id="key-a",
                capability_id="research.read", action="read",
                resource_scope="source:document-7",
                payload_digest=hashlib.sha256(b"approved-payload").hexdigest(),
                artifact_digest=ARTIFACT,
                runner_image_digest=hashlib.sha256(b"pinned-runner").hexdigest(),
                limits=limits,
            )
            approval = approvals.approve(
                "approver", intent["intent_id"], reason="Independent review of exact intent"
            )
            running = approvals.start("worker", approval["one_time_ticket"])
            self.assertEqual(running["status"], "running")
            self.assertTrue(approvals.check_running("worker", intent["intent_id"])["continue"])
            finalizing = approvals.begin_finalization("worker", intent["intent_id"], outcome="success")
            self.assertEqual(finalizing["status"], "finalizing")
            ledger = ExecutionReceiptLedger(
                authenticate=lambda session: self.sessions.get(session, {"authenticated": False}),
                authorize_writer=lambda principal, job: principal["subject"] == "worker:1",
                resolve_job=lambda workspace, job_id: approvals.get("worker", job_id),
                sign_digest=lambda digest: base64.b64encode(signing_key.sign(digest)).decode("ascii"),
                verify_signature=lambda digest, signature: self._verify_signature(signing_key, digest, signature),
                db_path=str(Path(self.temp.name) / "execution-receipts.sqlite3"),
            )
            receipt = ledger.append(
                "worker", intent_id=intent["intent_id"],
                policy_decision={
                    "allowed": True, "grant_id": approved_grant["grant_id"],
                    "evidence_run_id": decision["capability_evidence"]["run_id"],
                },
                started_at=finalizing["started_at"], finished_at=finalizing["finished_at"],
                exit_code=0,
                resource_usage={"wall_ms": 10000, "cpu_ms": 100, "memory_peak_mb": 64,
                                "output_bytes": 100, "pids_peak": 1},
                evidence_refs=["test-evidence:execution-output"],
            )
            self.assertEqual(receipt["receipt"]["intent_id"], intent["intent_id"])
            approvals.set_receipt_commit_verifier(
                lambda session, principal, intent_id, receipt_hash:
                    ledger.verify_committed_receipt(session, intent_id, receipt_hash)
            )
            terminal = approvals.complete_finalization(
                "worker", intent["intent_id"], receipt_hash=receipt["receipt_hash"]
            )
            self.assertEqual(terminal["status"], "completed")
            self.assertTrue(ledger.verify_chain("worker")["valid"])
        finally:
            if ledger is not None:
                ledger.close()
            approvals.close()

    def test_revoked_permission_stops_worker_checkpoint(self):
        request = self.request_grant()
        approved_grant = self.governance.approve("approver", request["grant_id"])
        self.verify_artifact()
        limits = {
            "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
            "pids": 32, "output_bytes": 100000,
        }
        approvals = ExecutionApprovalRegistry(
            authenticate=lambda session: self.sessions.get(session, {"authenticated": False}),
            authorize_request=lambda principal, intent: bool(self.authorize("owner")["allowed"]),
            authorize_approval=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_cancel=lambda principal, intent: principal["subject"] == "admin:1",
            authorize_executor=lambda principal, intent: principal["subject"] == "worker:1",
            validate_current_state=lambda principal, intent, stage: bool(self.authorize("owner")["allowed"]),
            db_path=str(Path(self.temp.name) / "revocation-approvals.sqlite3"),
        )
        try:
            intent = approvals.request_intent(
                "owner", entity_id="entity-a", key_id="key-a",
                capability_id="research.read", action="read",
                resource_scope="source:document-7",
                payload_digest=hashlib.sha256(b"approved-payload").hexdigest(),
                artifact_digest=ARTIFACT,
                runner_image_digest=hashlib.sha256(b"pinned-runner").hexdigest(),
                limits=limits,
            )
            approval = approvals.approve(
                "approver", intent["intent_id"], reason="Approved for revocation test"
            )
            approvals.start("worker", approval["one_time_ticket"])
            self.governance.revoke("approver", approved_grant["grant_id"], "revocation test")
            checkpoint = approvals.check_running("worker", intent["intent_id"])
            self.assertFalse(checkpoint["continue"])
            self.assertEqual(checkpoint["reason"], "execution_revoked_or_stale")
        finally:
            approvals.close()

    @staticmethod
    def _verify_signature(signing_key, digest, signature):
        try:
            signing_key.public_key().verify(base64.b64decode(signature), digest)
            return True
        except Exception:
            return False



if __name__ == "__main__":
    unittest.main()
