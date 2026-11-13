import base64
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from xparallel.execution_receipts import ExecutionReceiptLedger


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


class ExecutionReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.private = Ed25519PrivateKey.generate()
        self.public = self.private.public_key()
        self.job = {
            "workspace_id": "ws-a", "intent_id": "job:abc123",
            "intent_digest": sha("intent"), "status": "finalizing",
            "approver_subject": "reviewer:1", "decided_at": "2026-01-01T00:00:00+00:00",
            "started_at": "2026-01-01T00:01:00+00:00",
            "finished_at": "2026-01-01T00:01:10+00:00", "outcome": "success",
            "intent": {
                "entity_id": "entity-1234", "key_id": "key-a",
                "capability_id": "code.run", "action": "execute",
                "resource_scope": "workspace:project-1",
                "payload_digest": sha("payload"), "artifact_digest": sha("artifact"),
                "runner_image_digest": sha("runner"), "limits": {
                    "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000,
                    "pids": 32, "output_bytes": 100000,
                },
            },
        }
        self.ledger = ExecutionReceiptLedger(
            authenticate=lambda s: {"authenticated": True, "subject": "worker:1", "workspace_id": "ws-a"}
            if s == "worker" else {"authenticated": True, "subject": "other:1", "workspace_id": "ws-b"},
            authorize_writer=lambda p, job: p["subject"] == "worker:1",
            resolve_job=lambda ws, jid: self.job if ws == "ws-a" and jid == self.job["intent_id"] else None,
            sign_digest=lambda digest: base64.b64encode(self.private.sign(digest)).decode(),
            verify_signature=lambda digest, sig: self._verify(digest, sig),
            db_path=str(Path(self.temp.name) / "receipts.sqlite3"),
        )

    def _verify(self, digest, signature):
        try:
            self.public.verify(base64.b64decode(signature), digest)
            return True
        except Exception:
            return False

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def append(self):
        return self.ledger.append(
            "worker", intent_id=self.job["intent_id"],
            policy_decision={"allowed": True, "grant_id": "grant:one", "evidence_run_id": "vrun:one"},
            started_at=self.job["started_at"], finished_at=self.job["finished_at"],
            exit_code=0,
            resource_usage={"wall_ms": 10000, "cpu_ms": 9000, "memory_peak_mb": 128,
                            "output_bytes": 2048, "pids_peak": 4},
            evidence_refs=["artifact:stdout", "artifact:stderr"],
        )

    def test_receipt_is_signed_and_chain_verifies(self):
        result = self.append()
        self.assertEqual(result["receipt"]["artifact_digest"], sha("artifact"))
        self.assertTrue(self.ledger.verify_chain("worker")["valid"])
        self.assertIsNotNone(self.ledger.get_by_intent("worker", self.job["intent_id"]))

    def test_chain_links_multiple_receipts_and_prevents_duplicate_job(self):
        self.append()
        self.job["intent_id"] = "job:def456"
        self.job["intent_digest"] = sha("intent-2")
        result = self.append()
        self.assertNotEqual(result["previous_hash"], "0" * 64)
        self.assertEqual(self.ledger.verify_chain("worker")["verified_count"], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.append()

    def test_running_job_cannot_receive_receipt_before_finalization(self):
        self.job["status"] = "running"
        with self.assertRaises(ValueError):
            self.append()

    def test_receipt_must_match_authoritative_timestamps_and_outcome(self):
        with self.assertRaises(ValueError):
            self.ledger.append(
                "worker", intent_id="job:abc123",
                policy_decision={"allowed": True, "grant_id": "grant:one", "evidence_run_id": "vrun:one"},
                started_at="2026-01-01T00:00:00+00:00",
                finished_at=self.job["finished_at"], exit_code=0,
                resource_usage={"wall_ms": 1, "cpu_ms": 1, "memory_peak_mb": 1,
                                "output_bytes": 1, "pids_peak": 1},
                evidence_refs=["evidence:one"],
            )

    def test_resource_limits_and_policy_decision_are_enforced(self):
        with self.assertRaises(ValueError):
            self.ledger.append(
                "worker", intent_id="job:abc123",
                policy_decision={"allowed": False, "grant_id": "grant:one", "evidence_run_id": "vrun:one"},
                started_at=self.job["started_at"], finished_at=self.job["finished_at"],
                exit_code=0,
                resource_usage={"wall_ms": 10000, "cpu_ms": 9000, "memory_peak_mb": 9999,
                                "output_bytes": 2048, "pids_peak": 4},
                evidence_refs=["evidence:one"],
            )

    def test_workspace_and_writer_authority_are_enforced(self):
        with self.assertRaises(LookupError):
            self.ledger.append(
                "other", intent_id="job:abc123",
                policy_decision={"allowed": True, "grant_id": "grant:one", "evidence_run_id": "vrun:one"},
                started_at=self.job["started_at"], finished_at=self.job["finished_at"],
                exit_code=0,
                resource_usage={"wall_ms": 10000, "cpu_ms": 9000, "memory_peak_mb": 128,
                                "output_bytes": 2048, "pids_peak": 4},
                evidence_refs=["evidence:one"],
            )

    def test_receipt_table_rejects_update_and_delete(self):
        self.append()
        with self.assertRaises(Exception):
            self.ledger._db.execute("DELETE FROM execution_receipts")


if __name__ == "__main__":
    unittest.main()
