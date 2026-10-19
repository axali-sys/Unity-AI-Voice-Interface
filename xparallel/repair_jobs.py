"""SQLite-backed, workspace-scoped XParallel repair job records.

Jobs describe planning/diagnostics only. This module never executes a repair.
The database path follows XP_DB_PATH, matching the existing audit repository.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IS_SERVERLESS = os.getenv("VERCEL") == "1" or bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
DEFAULT_DB_PATH = os.getenv("XP_DB_PATH", "/tmp/.xparallel/xparallel.db" if IS_SERVERLESS else ".xparallel/xparallel.db")
DB_PATH = os.getenv("XP_REPAIR_JOBS_DB_PATH", DEFAULT_DB_PATH)
_LOCK = threading.Lock()
_MAX_JOBS = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect() -> sqlite3.Connection:
    if DB_PATH != ":memory:":
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=5)
    connection.row_factory = sqlite3.Row
    connection.execute("""
        CREATE TABLE IF NOT EXISTS repair_jobs (
            job_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            job_json TEXT NOT NULL
        )
    """)
    connection.execute("CREATE INDEX IF NOT EXISTS idx_repair_jobs_workspace_created ON repair_jobs(workspace_id, created_at DESC)")
    connection.commit()
    return connection


def create_job(*, workspace_id: str, actor: str, query: str, result: dict[str, Any], job_type: str = "diagnostic", status: str = "completed", error: str | None = None) -> dict[str, Any]:
    query = str(query).strip()
    if not query:
        raise ValueError("query_required")
    if len(query) > 4000:
        raise ValueError("query_too_large")
    if job_type not in {"diagnostic", "repair_plan"}:
        raise ValueError("unsupported_job_type")
    if status not in {"completed", "failed"}:
        raise ValueError("unsupported_job_status")
    now = _now()
    job = {
        "job_id": "xpr_" + uuid.uuid4().hex,
        "workspace_id": str(workspace_id)[:128],
        "job_type": job_type,
        "status": status,
        "stage": "plan",
        "query": query,
        "result": result,
        "error": error,
        "execution_performed": False,
        "approval_required_for_execution": True,
        "actor": str(actor)[:128],
        "created_at": now,
        "updated_at": now,
    }
    with _LOCK, closing(_connect()) as connection:
        connection.execute(
            "INSERT INTO repair_jobs(job_id, workspace_id, status, created_at, updated_at, job_json) VALUES (?, ?, ?, ?, ?, ?)",
            (job["job_id"], job["workspace_id"], job["status"], now, now, json.dumps(job, sort_keys=True)),
        )
        connection.execute("""
            DELETE FROM repair_jobs WHERE job_id IN (
                SELECT job_id FROM repair_jobs ORDER BY created_at DESC LIMIT -1 OFFSET ?
            )
        """, (_MAX_JOBS,))
        connection.commit()
    return job


def list_jobs(workspace_id: str, limit: int = 50, status: str = "") -> list[dict[str, Any]]:
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError):
        raise ValueError("invalid_limit")
    with _LOCK, _connect() as connection:
        if status:
            rows = connection.execute(
                "SELECT job_json FROM repair_jobs WHERE workspace_id=? AND status=? ORDER BY created_at DESC LIMIT ?",
                (workspace_id, status, limit),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT job_json FROM repair_jobs WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
                (workspace_id, limit),
            ).fetchall()
    return [json.loads(row["job_json"]) for row in rows]


def get_job(job_id: str, workspace_id: str) -> dict[str, Any] | None:
    with _LOCK, _connect() as connection:
        row = connection.execute(
            "SELECT job_json FROM repair_jobs WHERE job_id=? AND workspace_id=?",
            (job_id, workspace_id),
        ).fetchone()
    return json.loads(row["job_json"]) if row else None
