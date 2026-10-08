"""Persistent XParallel V1 experiment state machine.

The production boundary is intentionally not implemented here: approval records
intent to transfer, but no deployment or production execution occurs.
"""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .experiment import run_experiment

DB_PATH = os.getenv("XP_DB_PATH", ".xparallel/xparallel.db")
STATES = {
    "CREATED", "PLANNING", "PREPARING", "RUNNING", "OBSERVING", "TESTING",
    "FAILED", "DIAGNOSING", "REPAIRING", "VALIDATING", "VERIFIED",
    "APPROVAL_PENDING", "APPROVED", "REJECTED", "TRANSFERRING", "COMPLETED",
    "CANCELLED", "TIMEOUT", "BLOCKED", "SECURITY_REJECTED",
}
TRANSITIONS = {
    "CREATED": {"PLANNING", "CANCELLED"},
    "PLANNING": {"PREPARING", "BLOCKED", "CANCELLED"},
    "PREPARING": {"RUNNING", "BLOCKED", "SECURITY_REJECTED", "CANCELLED"},
    "RUNNING": {"OBSERVING", "FAILED", "TIMEOUT", "BLOCKED"},
    "OBSERVING": {"TESTING", "FAILED"},
    "TESTING": {"VALIDATING", "FAILED"},
    "FAILED": {"DIAGNOSING", "CANCELLED"},
    "DIAGNOSING": {"REPAIRING", "FAILED"},
    "REPAIRING": {"RUNNING", "FAILED"},
    "VALIDATING": {"VERIFIED", "FAILED"},
    "VERIFIED": {"APPROVAL_PENDING"},
    "APPROVAL_PENDING": {"APPROVED", "REJECTED"},
    "APPROVED": {"TRANSFERRING"},
    "TRANSFERRING": {"COMPLETED", "FAILED"},
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

class ExperimentStore:
    def __init__(self, path: str | None = None):
        self.path = path or DB_PATH
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.execute("""CREATE TABLE IF NOT EXISTS experiments (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            objective TEXT NOT NULL,
            constraints_json TEXT NOT NULL,
            success_criteria_json TEXT NOT NULL,
            state TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS experiment_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id TEXT NOT NULL,
            from_state TEXT,
            to_state TEXT NOT NULL,
            event_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        self.db.commit()

    def create(self, workspace_id: str, actor: str, objective: str,
               constraints: list[Any] | None = None,
               success_criteria: list[Any] | None = None,
               payload: dict[str, Any] | None = None) -> dict[str, Any]:
        eid = f"XP-{uuid.uuid4().hex[:8].upper()}"
        now = _now()
        record = {
            "id": eid, "workspace_id": workspace_id, "actor": actor,
            "objective": objective, "constraints": constraints or [],
            "success_criteria": success_criteria or [], "state": "CREATED",
            "payload": payload or {}, "created_at": now, "updated_at": now,
        }
        self.db.execute(
            "INSERT INTO experiments VALUES (?,?,?,?,?,?,?,?,?,?)",
            (eid, workspace_id, actor, objective, json.dumps(record["constraints"]),
             json.dumps(record["success_criteria"]), "CREATED", json.dumps(record["payload"]),
             now, now),
        )
        self.db.commit()
        self._event(eid, None, "CREATED", {"type": "created"})
        return record

    def get(self, eid: str) -> dict[str, Any] | None:
        row = self.db.execute(
            "SELECT id,workspace_id,actor,objective,constraints_json,success_criteria_json,state,payload_json,created_at,updated_at FROM experiments WHERE id=?",
            (eid,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row[0], "workspace_id": row[1], "actor": row[2],
            "objective": row[3], "constraints": json.loads(row[4]),
            "success_criteria": json.loads(row[5]), "state": row[6],
            "payload": json.loads(row[7]), "created_at": row[8], "updated_at": row[9],
        }

    def transition(self, eid: str, state: str, event: dict[str, Any] | None = None) -> dict[str, Any]:
        record = self.get(eid)
        if not record:
            raise KeyError("experiment_not_found")
        if state not in STATES:
            raise ValueError("invalid_state")
        current = record["state"]
        if state != current and state not in TRANSITIONS.get(current, set()):
            raise ValueError(f"invalid_transition:{current}->{state}")
        now = _now()
        self.db.execute("UPDATE experiments SET state=?,updated_at=? WHERE id=?", (state, now, eid))
        self.db.commit()
        self._event(eid, current if state != current else None, state, event or {})
        return self.get(eid)

    def _event(self, eid: str, previous: str | None, state: str, event: dict[str, Any]):
        self.db.execute(
            "INSERT INTO experiment_events(experiment_id,from_state,to_state,event_json,created_at) VALUES (?,?,?,?,?)",
            (eid, previous, state, json.dumps(event, sort_keys=True), _now()),
        )
        self.db.commit()

    def events(self, eid: str) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT from_state,to_state,event_json,created_at FROM experiment_events WHERE experiment_id=? ORDER BY id",
            (eid,),
        ).fetchall()
        return [{"from": r[0], "to": r[1], "event": json.loads(r[2]), "created_at": r[3]} for r in rows]

    def run(self, eid: str) -> dict[str, Any]:
        record = self.get(eid)
        if not record:
            raise KeyError("experiment_not_found")
        if record["state"] not in {"CREATED", "APPROVAL_PENDING"}:
            raise ValueError(f"cannot_run_from:{record['state']}")
        if record["state"] == "APPROVAL_PENDING":
            return record
        try:
            self.transition(eid, "PLANNING")
            self.transition(eid, "PREPARING")
            self.transition(eid, "RUNNING")
            execution = record["payload"].get("execution")
            result = run_experiment(record["objective"], execution)
            self.db.execute(
                "UPDATE experiments SET payload_json=?,updated_at=? WHERE id=?",
                (json.dumps({"execution": execution, "result": result}, sort_keys=True), _now(), eid),
            )
            self.db.commit()
            self.transition(eid, "OBSERVING", {"result_status": result.get("result", {}).get("status")})
            self.transition(eid, "TESTING")
            status = result.get("result", {}).get("status")
            if status == "blocked":
                self.transition(eid, "BLOCKED", {"result": result.get("result")})
                return self.get(eid)
            if status != "success":
                self.transition(eid, "FAILED", {"result": result.get("result")})
                return self.get(eid)
            self.transition(eid, "VALIDATING")
            self.transition(eid, "VERIFIED", {"evidence": result.get("result")})
            self.transition(eid, "APPROVAL_PENDING", {"requires_human_approval": True})
            return self.get(eid)
        except Exception as exc:
            current = self.get(eid)
            if current and current["state"] not in {"FAILED", "BLOCKED", "CANCELLED"}:
                try:
                    self.transition(eid, "FAILED", {"error": str(exc)})
                except ValueError:
                    pass
            raise

    def approve(self, eid: str, actor: str) -> dict[str, Any]:
        record = self.get(eid)
        if not record:
            raise KeyError("experiment_not_found")
        if record["state"] != "APPROVAL_PENDING":
            raise ValueError(f"cannot_approve_from:{record['state']}")
        return self.transition(eid, "APPROVED", {"approved_by": actor, "production_execution": False})

    def reject(self, eid: str, actor: str, reason: str = "") -> dict[str, Any]:
        record = self.get(eid)
        if not record:
            raise KeyError("experiment_not_found")
        if record["state"] != "APPROVAL_PENDING":
            raise ValueError(f"cannot_reject_from:{record['state']}")
        return self.transition(eid, "REJECTED", {"rejected_by": actor, "reason": reason})

STORE = ExperimentStore()
