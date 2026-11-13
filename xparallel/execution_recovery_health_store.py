"""Optional persistent, secret-free recovery health history."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any


class SQLiteExecutionRecoveryHealthStore:
    """Persist aggregate recovery health on an explicitly selected host volume.

    Only timestamps, counters, bounded batch totals and exception class names
    are stored. No sessions, payloads, exception messages or adapter details.
    """

    def __init__(self, *, db_path: str):
        if not isinstance(db_path, str) or not db_path.strip():
            raise ValueError("explicit_recovery_health_database_path_required")
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS recovery_health_events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL CHECK(event_type IN ('success','failure')),
                recorded_at TEXT NOT NULL,
                error_type TEXT,
                scanned INTEGER,
                recovered INTEGER,
                pending INTEGER,
                CHECK (
                    (event_type='failure' AND error_type IS NOT NULL
                     AND scanned IS NULL AND recovered IS NULL AND pending IS NULL)
                    OR
                    (event_type='success' AND error_type IS NULL
                     AND scanned >= 0 AND recovered >= 0 AND pending >= 0)
                )
            )
        """)
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS recovery_health_no_update
            BEFORE UPDATE ON recovery_health_events BEGIN
                SELECT RAISE(ABORT, 'recovery_health_history_is_append_only');
            END
        """)
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS recovery_health_no_delete
            BEFORE DELETE ON recovery_health_events BEGIN
                SELECT RAISE(ABORT, 'recovery_health_history_is_append_only');
            END
        """)
        self._db.commit()

    def record_success(self, *, recorded_at: str, scanned: int,
                       recovered: int, pending: int) -> None:
        values = (scanned, recovered, pending)
        if (not isinstance(recorded_at, str) or not recorded_at
                or any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for v in values)
                or recovered + pending > scanned):
            raise ValueError("invalid_recovery_health_success_event")
        with self._lock, self._db:
            self._db.execute(
                """INSERT INTO recovery_health_events
                   (event_type, recorded_at, scanned, recovered, pending)
                   VALUES ('success', ?, ?, ?, ?)""",
                (recorded_at, scanned, recovered, pending),
            )

    def record_failure(self, *, recorded_at: str, error_type: str) -> None:
        if (not isinstance(recorded_at, str) or not recorded_at
                or not isinstance(error_type, str)
                or not error_type.isidentifier() or len(error_type) > 80):
            raise ValueError("invalid_recovery_health_failure_event")
        with self._lock, self._db:
            self._db.execute(
                """INSERT INTO recovery_health_events
                   (event_type, recorded_at, error_type)
                   VALUES ('failure', ?, ?)""",
                (recorded_at, error_type),
            )

    def load_state(self) -> dict[str, Any]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM recovery_health_events ORDER BY sequence"
            ).fetchall()
        state = {
            "last_cycle_at": None, "last_success_at": None,
            "last_error_type": None, "consecutive_failures": 0,
            "total_failures": 0, "total_recovered": 0, "last_result": None,
        }
        for row in rows:
            state["last_cycle_at"] = row["recorded_at"]
            if row["event_type"] == "failure":
                state["last_error_type"] = row["error_type"]
                state["consecutive_failures"] += 1
                state["total_failures"] += 1
            else:
                state["last_success_at"] = row["recorded_at"]
                state["last_error_type"] = None
                state["consecutive_failures"] = 0
                state["total_recovered"] += row["recovered"]
                state["last_result"] = {
                    "scanned": row["scanned"],
                    "recovered": row["recovered"],
                    "pending": row["pending"],
                }
        return state

    def close(self) -> None:
        with self._lock:
            self._db.close()
