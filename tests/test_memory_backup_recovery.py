import tempfile
import unittest
from pathlib import Path

from xparallel.memory_vault import list_memories, save_memory
from xparallel.memory_backup import create_snapshot, verify_snapshot, list_snapshots
from xparallel.memory_recovery import recover_snapshot


class MemoryBackupRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp_dir.name) / "continuity.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_snapshot_round_trip_and_integrity(self):
        save_memory("durable identity record", "alpha", db_path=self.db)
        snapshot = create_snapshot("alpha", self.db)
        checked = verify_snapshot(snapshot["snapshot_id"], "alpha", self.db)
        self.assertTrue(checked["valid"])
        self.assertEqual(checked["item_count"], 1)
        self.assertEqual(len(list_snapshots("alpha", db_path=self.db)), 1)

    def test_recovery_requires_authorization_and_scope(self):
        save_memory("durable record", "alpha", db_path=self.db)
        snap = create_snapshot("alpha", self.db)
        result = recover_snapshot(snap["snapshot_id"], "alpha", db_path=self.db)
        self.assertFalse(result["recovered"])
        self.assertEqual(result["reason"], "recovery_requires_authorization_and_scope")

    def test_merge_recovers_to_explicit_destination_workspace(self):
        save_memory("restorable source", "source", db_path=self.db)
        snap = create_snapshot("source", self.db)
        result = recover_snapshot(snap["snapshot_id"], "source", "target",
                                  authorized=True, explicit_scope=True,
                                  db_path=self.db)
        self.assertTrue(result["recovered"])
        self.assertEqual(result["restored_count"], 1)
        self.assertEqual(list_memories("target", db_path=self.db)[0]["content"],
                         "restorable source")

    def test_replace_recovery_replaces_only_target_workspace(self):
        save_memory("snapshot value", "alpha", db_path=self.db)
        snap = create_snapshot("alpha", self.db)
        save_memory("new target-only value", "alpha", db_path=self.db)
        save_memory("untouched other workspace", "beta", db_path=self.db)
        result = recover_snapshot(snap["snapshot_id"], "alpha", mode="replace",
                                  authorized=True, explicit_scope=True,
                                  db_path=self.db)
        self.assertTrue(result["recovered"])
        self.assertEqual([m["content"] for m in list_memories("alpha", db_path=self.db)],
                         ["snapshot value"])
        self.assertEqual(list_memories("beta", db_path=self.db)[0]["content"],
                         "untouched other workspace")

    def test_corrupted_snapshot_is_rejected(self):
        save_memory("verify me", "alpha", db_path=self.db)
        snap = create_snapshot("alpha", self.db)
        from xparallel.memory_vault import _connect
        with _connect(self.db) as conn:
            conn.execute("UPDATE memory_snapshots SET payload_json=? WHERE snapshot_id=?",
                        ('{"corrupt":true}', snap["snapshot_id"]))
        result = recover_snapshot(snap["snapshot_id"], "alpha",
                                  authorized=True, explicit_scope=True,
                                  db_path=self.db)
        self.assertFalse(result["recovered"])
        self.assertEqual(result["reason"], "integrity_mismatch")

    def test_recovery_never_reads_snapshot_from_other_workspace(self):
        save_memory("private alpha", "alpha", db_path=self.db)
        snap = create_snapshot("alpha", self.db)
        result = recover_snapshot(snap["snapshot_id"], "beta",
                                  authorized=True, explicit_scope=True,
                                  db_path=self.db)
        self.assertFalse(result["recovered"])
        self.assertEqual(result["reason"], "snapshot_not_found")


if __name__ == "__main__":
    unittest.main()
