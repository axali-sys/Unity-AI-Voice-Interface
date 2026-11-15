"""Durable SQLite repository for XParallel worker leases.

Uses a dedicated database file and private tables. It does not alter the
Parallel Verse or execution-approval databases. Production hosts may replace
this adapter with an equivalent transactional repository.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteWorkerLeaseRepository:
    """Atomic workspace/task lease store with append-only lifecycle events."""

    def __init__(self, path: str):
        if not isinstance(path, str) or not path.strip():
            raise ValueError("worker_lease_database_path_required")
        self.path = path
        if path != ":memory:":
            Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS worker_leases (
                    workspace_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    lease_id TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('active','released')),
                    version INTEGER NOT NULL CHECK(version >= 1),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(workspace_id, task_id),
                    UNIQUE(lease_id)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS worker_lease_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workspace_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    lease_id TEXT NOT NULL,
                    worker_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    detail_json TEXT NOT NULL
                )
            """)

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    @staticmethod
    def _event(db: sqlite3.Connection, workspace: str, task: str,
               lease: str, worker: str, event: str, detail: dict[str, Any]) -> None:
        db.execute(
            """INSERT INTO worker_lease_events
               (workspace_id,task_id,lease_id,worker_id,event_type,occurred_at,detail_json)
               VALUES (?,?,?,?,?,?,?)""",
            (workspace, task, lease, worker, event, _now(),
             json.dumps(detail, sort_keys=True, separators=(",", ":"))),
        )

    def claim(self, workspace_id: str, task_id: str, agent_id: str,
              worker_id: str, lease_id: str, expires_at: str) -> dict[str, Any]:
        now = _now()
        expiry = datetime.fromisoformat(expires_at)
        if expiry.tzinfo is None or expiry.astimezone(timezone.utc) <= datetime.now(timezone.utc):
            raise ValueError("worker_lease_expiry_must_be_future_aware")
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT * FROM worker_leases WHERE workspace_id=? AND task_id=?",
                (workspace_id, task_id),
            ).fetchone()
            if old is not None and old["status"] == "active":
                old_expiry = datetime.fromisoformat(old["expires_at"])
                if old_expiry.tzinfo is not None and old_expiry.astimezone(timezone.utc) > datetime.now(timezone.utc):
                    raise PermissionError("worker_lease_already_claimed")
            version = int(old["version"]) + 1 if old is not None else 1
            db.execute(
                """INSERT INTO worker_leases
                   (workspace_id,task_id,agent_id,worker_id,lease_id,expires_at,status,version,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,'active',?,?,?)
                   ON CONFLICT(workspace_id,task_id) DO UPDATE SET
                     agent_id=excluded.agent_id, worker_id=excluded.worker_id,
                     lease_id=excluded.lease_id, expires_at=excluded.expires_at,
                     status='active', version=excluded.version, updated_at=excluded.updated_at""",
                (workspace_id, task_id, agent_id, worker_id, lease_id,
                 expiry.astimezone(timezone.utc).isoformat(), version, now, now),
            )
            self._event(db, workspace_id, task_id, lease_id, worker_id,
                        "lease_claimed" if old is None else "lease_reclaimed",
                        {"version": version})
            row = db.execute(
                "SELECT * FROM worker_leases WHERE workspace_id=? AND task_id=?",
                (workspace_id, task_id),
            ).fetchone()
            db.commit()
            return dict(row)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, workspace_id: str, task_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM worker_leases WHERE workspace_id=? AND task_id=?",
                (workspace_id, task_id),
            ).fetchone()
            return self._row(row)

    def renew(self, workspace_id: str, task_id: str, lease_id: str,
              worker_id: str, expected_version: int, expires_at: str) -> dict[str, Any]:
        expiry = datetime.fromisoformat(expires_at)
        now_dt = datetime.now(timezone.utc)
        if expiry.tzinfo is None or expiry.astimezone(timezone.utc) <= now_dt:
            raise ValueError("worker_lease_expiry_must_be_future_aware")
        now = now_dt.isoformat()
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute(
                """UPDATE worker_leases SET expires_at=?,version=version+1,updated_at=?
                   WHERE workspace_id=? AND task_id=? AND lease_id=? AND worker_id=?
                     AND status='active' AND version=? AND expires_at>?""",
                (expiry.astimezone(timezone.utc).isoformat(), now, workspace_id,
                 task_id, lease_id, worker_id, expected_version, now),
            )
            if cur.rowcount != 1:
                raise PermissionError("worker_lease_stale_expired_or_not_owned")
            self._event(db, workspace_id, task_id, lease_id, worker_id,
                        "lease_renewed", {"version": expected_version + 1})
            row = db.execute(
                "SELECT * FROM worker_leases WHERE workspace_id=? AND task_id=?",
                (workspace_id, task_id),
            ).fetchone()
            db.commit()
            return dict(row)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def release(self, workspace_id: str, task_id: str, lease_id: str,
                worker_id: str, expected_version: int) -> dict[str, Any]:
        now = _now()
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            cur = db.execute(
                """UPDATE worker_leases SET status='released',version=version+1,updated_at=?
                   WHERE workspace_id=? AND task_id=? AND lease_id=? AND worker_id=?
                     AND status='active' AND version=?""",
                (now, workspace_id, task_id, lease_id, worker_id, expected_version),
            )
            if cur.rowcount != 1:
                raise PermissionError("worker_lease_stale_or_not_owned")
            self._event(db, workspace_id, task_id, lease_id, worker_id,
                        "lease_released", {"version": expected_version + 1})
            row = db.execute(
                "SELECT * FROM worker_leases WHERE workspace_id=? AND task_id=?",
                (workspace_id, task_id),
            ).fetchone()
            db.commit()
            return dict(row)
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def list_events(self, workspace_id: str, task_id: str,
                    limit: int = 100) -> list[dict[str, Any]]:
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValueError("worker_lease_event_limit_out_of_range")
        with self._connect() as db:
            rows = db.execute(
                """SELECT event_id,workspace_id,task_id,lease_id,worker_id,event_type,
                          occurred_at,detail_json
                   FROM worker_lease_events WHERE workspace_id=? AND task_id=?
                   ORDER BY event_id DESC LIMIT ?""",
                (workspace_id, task_id, limit),
            ).fetchall()
            return [{**dict(row), "detail": json.loads(row["detail_json"])} for row in rows]
