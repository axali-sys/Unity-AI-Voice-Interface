import sqlite3
import tempfile
import unittest
from pathlib import Path

from xparallel.storage_recovery import Migration, SQLiteJSONRepository, SQLiteStore


class SQLiteStorageRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = SQLiteStore(
            str(self.root / "state.sqlite3"),
            authorize_restore=lambda approval: approval == "approved",
        )
        self.repo = SQLiteJSONRepository(self.store)

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_repository_is_workspace_scoped_and_transactional(self):
        self.repo.put("ws-a", "item:1", {"value": 1})
        self.repo.put("ws-b", "item:1", {"value": 2})
        self.assertEqual(self.repo.get("ws-a", "item:1"), {"value": 1})
        self.assertEqual(self.repo.get("ws-b", "item:1"), {"value": 2})
        with self.assertRaises(RuntimeError):
            with self.store.transaction() as db:
                db.execute("INSERT INTO workspace_records VALUES (?, ?, ?, ?)",
                           ("ws-a", "rollback", "{}", "2026-01-01T00:00:00+00:00"))
                raise RuntimeError("rollback")
        self.assertIsNone(self.repo.get("ws-a", "rollback"))

    def test_migrations_are_ordered_idempotent_and_checksum_protected(self):
        migration = Migration(2, ("CREATE TABLE sample (id INTEGER PRIMARY KEY)",))
        self.assertEqual(self.store.apply_migrations([migration]), 1)
        self.assertEqual(self.store.apply_migrations([migration]), 0)
        with self.assertRaises(ValueError):
            self.store.apply_migrations([Migration(2, ("CREATE TABLE changed (id INTEGER)",))])
        with self.assertRaises(ValueError):
            self.store.apply_migrations([Migration(4, ("CREATE TABLE gap (id INTEGER)",))])

    def test_backup_integrity_and_restore_recover_previous_state(self):
        self.repo.put("ws-a", "original", {"version": "before"})
        backup = self.store.backup(str(self.root / "snapshot.sqlite3"))
        self.assertEqual(backup["integrity"], "ok")
        self.repo.put("ws-a", "original", {"version": "after"})
        self.repo.put("ws-a", "extra", {"temporary": True})
        result = self.store.restore_from(backup["path"], "approved")
        self.assertTrue(result["restored"])
        self.assertEqual(self.repo.get("ws-a", "original"), {"version": "before"})
        self.assertIsNone(self.repo.get("ws-a", "extra"))
        self.assertTrue(SQLiteStore.verify_database(backup["path"])["valid"])
        self.assertTrue(Path(result["safety_backup"]).is_file())

    def test_restore_requires_explicit_authorization(self):
        backup = self.store.backup(str(self.root / "snapshot.sqlite3"))
        with self.assertRaises(PermissionError):
            self.store.restore_from(backup["path"], "no")

    def test_backup_refuses_overwrite_and_invalid_destination(self):
        destination = self.root / "snapshot.sqlite3"
        self.store.backup(str(destination))
        with self.assertRaises(FileExistsError):
            self.store.backup(str(destination))
        with self.assertRaises(ValueError):
            self.store.backup(str(self.root / "state.sqlite3"))

    def test_backup_retention_keeps_newest_files(self):
        paths = []
        for index in range(4):
            path = self.root / f"xp-backup-{index}.sqlite3"
            path.write_bytes(b"test")
            paths.append(path)
        result = SQLiteStore.prune_backups(str(self.root), prefix="xp-backup-", keep=2)
        self.assertEqual(len(result["kept"]), 2)
        self.assertEqual(len(result["removed"]), 2)
        self.assertEqual(sum(path.exists() for path in paths), 2)

    def test_migration_gaps_and_invalid_restore_adapter_are_rejected(self):
        with self.assertRaises(TypeError):
            SQLiteStore(str(self.root / "bad.sqlite3"), authorize_restore=None)
        with self.assertRaises(ValueError):
            Migration(0, ("CREATE TABLE x (id INTEGER)",))


if __name__ == "__main__":
    unittest.main()
