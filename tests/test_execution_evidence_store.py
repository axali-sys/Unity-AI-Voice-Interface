import tempfile
import unittest
from pathlib import Path

from xparallel.execution_evidence_store import SQLiteExecutionEvidenceStore


class SQLiteExecutionEvidenceStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.tmp.name) / "evidence.sqlite3")
        self.session = {"subject": "operator:1", "workspace_id": "workspace-a"}
        self.store = SQLiteExecutionEvidenceStore(
            authenticate=lambda session: {
                "authenticated": True, "subject": session["subject"],
                "workspace_id": session["workspace_id"],
            },
            authorize_read=lambda principal, record: principal["workspace_id"] == record["workspace_id"],
            sanitize_result=lambda result: {
                "status": result["status"],
                "stdout": result.get("stdout", ""),
                "stderr": result.get("stderr", ""),
            },
            db_path=self.path,
        )
        self.intent = {"workspace_id": "workspace-a", "intent_id": "intent:1"}

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_persists_content_addressed_evidence_and_reads_it(self):
        stored = self.store.store_evidence(
            {"status": "success", "stdout": "ok", "secret": "must-not-persist"},
            self.intent,
        )
        self.assertTrue(stored["durable"])
        self.assertEqual(stored["storage"], "sqlite-persistent-volume")
        read = self.store.read_evidence(self.session, stored["references"][0])
        self.assertEqual(read["record"]["result"], {"status": "success", "stdout": "ok", "stderr": ""})
        self.assertNotIn("secret", read["record"]["result"])

    def test_rejects_cross_workspace_read(self):
        stored = self.store.store_evidence({"status": "failed"}, self.intent)
        other = {"subject": "other", "workspace_id": "workspace-b"}
        with self.assertRaisesRegex(PermissionError, "workspace_mismatch"):
            self.store.read_evidence(other, stored["references"][0])

    def test_rejects_read_when_authorizer_denies(self):
        self.store._authorize_read = lambda principal, record: False
        stored = self.store.store_evidence({"status": "failed"}, self.intent)
        with self.assertRaisesRegex(PermissionError, "not_authorized"):
            self.store.read_evidence(self.session, stored["references"][0])

    def test_rejects_invalid_intent_scope(self):
        with self.assertRaisesRegex(ValueError, "workspace_required"):
            self.store.store_evidence({"status": "failed"}, {"intent_id": "intent:1"})

    def test_rejects_modified_reference_digest(self):
        stored = self.store.store_evidence({"status": "success"}, self.intent)
        ref = stored["references"][0]
        bad = ref[:-1] + ("0" if ref[-1] != "0" else "1")
        with self.assertRaises(LookupError):
            self.store.read_evidence(self.session, bad)

    def test_database_enforces_append_only_rows(self):
        self.store.store_evidence({"status": "success"}, self.intent)
        with self.assertRaises(Exception):
            self.store._db.execute("DELETE FROM execution_evidence")


if __name__ == "__main__":
    unittest.main()
