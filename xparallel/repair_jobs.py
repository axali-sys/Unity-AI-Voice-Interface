"""Workspace-scoped repair job records. Jobs are plans/diagnostics, never implicit execution."""
from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

IS_SERVERLESS = os.getenv("VERCEL") == "1" or bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
DEFAULT_FILE = "/tmp/xparallel/repair_jobs.json" if IS_SERVERLESS else "xparallel/data/repair_jobs.json"
DATA_FILE = Path(os.getenv("XP_REPAIR_JOBS_FILE", DEFAULT_FILE))
_LOCK = threading.Lock()
_MAX_JOBS = 500


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read() -> list[dict]:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        return []
    try:
        value = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return value if isinstance(value, list) else []


def _write(items: list[dict]) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(DATA_FILE.suffix + ".tmp")
    temporary.write_text(json.dumps(items[-_MAX_JOBS:], indent=2), encoding="utf-8")
    temporary.replace(DATA_FILE)


def create_job(*, workspace_id: str, actor: str, query: str, result: dict, job_type: str = "diagnostic") -> dict:
    query = str(query).strip()
    if not query:
        raise ValueError("query_required")
    if len(query) > 4000:
        raise ValueError("query_too_large")
    if job_type not in {"diagnostic", "repair_plan"}:
        raise ValueError("unsupported_job_type")
    job = {
        "job_id": "xpr_" + uuid.uuid4().hex,
        "workspace_id": str(workspace_id)[:128],
        "job_type": job_type,
        "status": "completed",
        "stage": "plan",
        "query": query,
        "result": result,
        "error": None,
        "execution_performed": False,
        "approval_required_for_execution": True,
        "actor": str(actor)[:128],
        "created_at": _now(),
        "updated_at": _now(),
    }
    with _LOCK:
        items = _read()
        items.append(job)
        _write(items)
    return job


def list_jobs(workspace_id: str, limit: int = 50, status: str = "") -> list[dict]:
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError):
        raise ValueError("invalid_limit")
    with _LOCK:
        items = _read()
    selected = [
        item for item in items
        if item.get("workspace_id") == workspace_id
        and (not status or item.get("status") == status)
    ]
    return list(reversed(selected[-limit:]))


def get_job(job_id: str, workspace_id: str) -> dict | None:
    with _LOCK:
        items = _read()
    for item in reversed(items):
        if item.get("job_id") == job_id and item.get("workspace_id") == workspace_id:
            return item
    return None
