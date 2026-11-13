import sqlite3
import tempfile
import unittest
from pathlib import Path

from xparallel.execution_recovery_health_store import SQLiteExecutionRecoveryHealthStore


class SQLiteExecutionRecoveryHealthStoreTests(unittest.TestCase):
    def test_history_survives_close_and_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "health.sqlite3")
            store = SQLiteExecutionRecoveryHealthStore(db_path=path)
            store.record_success(recorded_at="2026-11-14T10:00:00+00:00", scanned=3, recovered=2, pending=1)
            store.record_failure(recorded_at="2026-11-14T10:01:00+00:00", error_type="TimeoutError")
            store.close()

            reopened = SQLiteExecutionRecoveryHealthStore(db_path=path)
            state = reopened.load_state()
            reopened.close()
            self.assertEqual(state["last_cycle_at"], "2026-11-14T10:01:00+00:00")
            self.assertEqual(state["last_success_at"], "2026-11-14T10:00:00+00:00")
            self.assertEqual(state["last_error_type"], "TimeoutError")
            self.assertEqual(state["consecutive_failures"], 1)
            self.assertEqual(state["total_failures"], 1)
            self.assertEqual(state["total_recovered"], 2)
            self.assertEqual(state["last_result"], {"scanned": 3, "recovered": 2, "pending": 1})

    def test_success_resets_consecutive_failures_but_preserves_total(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteExecutionRecoveryHealthStore(db_path=str(Path(directory) / "health.db"))
            store.record_failure(recorded_at="t1", error_type="OSError")
            store.record_success(recorded_at="t2", scanned=0, recovered=0, pending=0)
            state = store.load_state()
            store.close()
            self.assertEqual(state["consecutive_failures"], 0)
            self.assertEqual(state["total_failures"], 1)
            self.assertIsNone(state["last_error_type"])

    def test_append_only_history_rejects_update_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteExecutionRecoveryHealthStore(db_path=str(Path(directory) / "health.db"))
            store.record_success(recorded_at="t1", scanned=0, recovered=0, pending=0)
            with self.assertRaises(sqlite3.IntegrityError):
                store._db.execute("UPDATE recovery_health_events SET pending=1")
            with self.assertRaises(sqlite3.IntegrityError):
                store._db.execute("DELETE FROM recovery_health_events")
            store.close()

    def test_rejects_sensitive_or_invalid_error_type(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteExecutionRecoveryHealthStore(db_path=str(Path(directory) / "health.db"))
            with self.assertRaises(ValueError):
                store.record_failure(recorded_at="t1", error_type="token=secret")
            store.close()


if __name__ == "__main__":
    unittest.main()
