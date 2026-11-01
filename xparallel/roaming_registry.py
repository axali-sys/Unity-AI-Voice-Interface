"""Persistent registry for authenticated roaming XParallel runtimes.

The registry stores endpoint metadata and hashed per-runtime credentials.
It never proxies traffic itself; clients discover a healthy runtime and connect
to it using their own authenticated transport.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from urllib.parse import urlparse

DEFAULT_TTL_SECONDS = 180
MAX_TTL_SECONDS = 3600
_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{1,79}$")


def _db_path() -> str:
    return os.getenv("XP_ROAMING_DB", "xparallel_roaming.sqlite3")


def _connect():
    conn = sqlite3.connect(_db_path(), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS roaming_runtimes (
            runtime_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            base_url TEXT NOT NULL,
            capabilities TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'offline',
            created_at REAL NOT NULL,
            last_seen REAL NOT NULL,
            expires_at REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_roaming_status_expiry ON roaming_runtimes(status, expires_at)")
    conn.execute("""CREATE TABLE IF NOT EXISTS roaming_tasks (
        task_id TEXT PRIMARY KEY, runtime_id TEXT NOT NULL, task_type TEXT NOT NULL,
        payload TEXT NOT NULL, workspace_id TEXT NOT NULL, status TEXT NOT NULL,
        result TEXT, attempts INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL,
        updated_at REAL NOT NULL, claimed_at REAL, lease_until REAL, completed_at REAL,
        FOREIGN KEY(runtime_id) REFERENCES roaming_runtimes(runtime_id)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_roaming_tasks_queue ON roaming_tasks(runtime_id, status, created_at)")
    return conn


@contextmanager
def _db():
    conn = _connect()
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def _validate_base_url(value: str) -> str:
    value = str(value or "").strip().rstrip("/")
    parsed = urlparse(value)
    local_ok = parsed.hostname in {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and not (local_ok and parsed.scheme == "http"):
        raise ValueError("runtime_url_must_use_https")
    if not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("runtime_url_invalid")
    if parsed.path not in ("", "/"):
        raise ValueError("runtime_url_must_be_origin")
    return value


def _normalise_capabilities(value) -> list[str]:
    if not isinstance(value, list):
        raise ValueError("capabilities_must_be_list")
    items = sorted({str(x).strip().lower() for x in value if str(x).strip()})
    if len(items) > 40 or any(len(x) > 64 for x in items):
        raise ValueError("capabilities_invalid")
    return items


def _public(row, include_token=False):
    item = {
        "runtime_id": row["runtime_id"],
        "name": row["name"],
        "base_url": row["base_url"],
        "capabilities": json.loads(row["capabilities"]),
        "status": row["status"],
        "created_at": row["created_at"],
        "last_seen": row["last_seen"],
        "expires_at": row["expires_at"],
    }
    if include_token:
        item["runtime_token"] = row["runtime_token"]
    return item


def register_runtime(runtime_id: str, name: str, base_url: str, capabilities, ttl_seconds=DEFAULT_TTL_SECONDS) -> dict:
    runtime_id = str(runtime_id or "").strip()
    name = str(name or "").strip()
    if not _ID_RE.fullmatch(runtime_id):
        raise ValueError("runtime_id_invalid")
    if not name or len(name) > 120:
        raise ValueError("runtime_name_invalid")
    base_url = _validate_base_url(base_url)
    capabilities = _normalise_capabilities(capabilities)
    ttl = max(30, min(int(ttl_seconds), MAX_TTL_SECONDS))
    now = time.time()
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    with _db() as conn:
        conn.execute("""
            INSERT INTO roaming_runtimes
                (runtime_id, name, base_url, capabilities, token_hash, status, created_at, last_seen, expires_at)
            VALUES (?, ?, ?, ?, ?, 'online', ?, ?, ?)
            ON CONFLICT(runtime_id) DO UPDATE SET
                name=excluded.name, base_url=excluded.base_url,
                capabilities=excluded.capabilities, token_hash=excluded.token_hash,
                status='online', last_seen=excluded.last_seen, expires_at=excluded.expires_at
        """, (runtime_id, name, base_url, json.dumps(capabilities), token_hash, now, now, now + ttl))
        row = conn.execute("SELECT * FROM roaming_runtimes WHERE runtime_id=?", (runtime_id,)).fetchone()
    result = _public(row)
    result["runtime_token"] = token  # shown once; only its hash is persisted
    return result


def heartbeat(runtime_id: str, runtime_token: str, ttl_seconds=DEFAULT_TTL_SECONDS) -> dict:
    runtime_id = str(runtime_id or "").strip()
    token_hash = hashlib.sha256(str(runtime_token or "").encode()).hexdigest()
    ttl = max(30, min(int(ttl_seconds), MAX_TTL_SECONDS))
    now = time.time()
    with _db() as conn:
        row = conn.execute("SELECT token_hash FROM roaming_runtimes WHERE runtime_id=?", (runtime_id,)).fetchone()
        if not row or not secrets.compare_digest(row["token_hash"], token_hash):
            raise PermissionError("runtime_authentication_failed")
        conn.execute(
            "UPDATE roaming_runtimes SET status='online', last_seen=?, expires_at=? WHERE runtime_id=?",
            (now, now + ttl, runtime_id),
        )
        updated = conn.execute("SELECT * FROM roaming_runtimes WHERE runtime_id=?", (runtime_id,)).fetchone()
    return _public(updated)


def discover(capability: str | None = None, limit=20) -> list[dict]:
    now = time.time()
    limit = max(1, min(int(limit), 100))
    with _db() as conn:
        conn.execute("UPDATE roaming_runtimes SET status='offline' WHERE expires_at <= ? AND status='online'", (now,))
        if capability:
            rows = conn.execute(
                "SELECT * FROM roaming_runtimes WHERE status='online' AND expires_at>? ORDER BY last_seen DESC LIMIT ?",
                (now, limit * 4),
            ).fetchall()
            wanted = str(capability).strip().lower()
            rows = [row for row in rows if wanted in json.loads(row["capabilities"])][:limit]
        else:
            rows = conn.execute(
                "SELECT * FROM roaming_runtimes WHERE status='online' AND expires_at>? ORDER BY last_seen DESC LIMIT ?",
                (now, limit),
            ).fetchall()
    return [_public(row) for row in rows]


def registry_status() -> dict:
    services = discover(limit=100)
    return {
        "service": "xparallel-roaming-registry",
        "status": "online",
        "online_runtimes": len(services),
        "runtimes": services,
        "execution_performed": False,
    }


def enqueue_task(runtime_id: str, task_type: str, payload: dict, workspace_id: str = "default") -> dict:
    """Queue a bounded JSON task for one registered runtime; never executes it here."""
    runtime_id = str(runtime_id or "").strip()
    task_type = str(task_type or "").strip().lower()
    workspace_id = str(workspace_id or "default").strip()[:120]
    if not _ID_RE.fullmatch(runtime_id):
        raise ValueError("runtime_id_invalid")
    if not task_type or len(task_type) > 64:
        raise ValueError("task_type_invalid")
    if not isinstance(payload, dict):
        raise ValueError("task_payload_must_be_object")
    encoded = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > 64000:
        raise ValueError("task_payload_too_large")
    now = time.time()
    task_id = secrets.token_urlsafe(18)
    with _db() as conn:
        runtime = conn.execute(
            "SELECT runtime_id FROM roaming_runtimes WHERE runtime_id=? AND status='online' AND expires_at>?",
            (runtime_id, now),
        ).fetchone()
        if not runtime:
            raise LookupError("runtime_not_online")
        conn.execute("""
            INSERT INTO roaming_tasks
                (task_id, runtime_id, task_type, payload, workspace_id, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)
        """, (task_id, runtime_id, task_type, encoded, workspace_id, now, now))
    return {"task_id": task_id, "runtime_id": runtime_id, "status": "queued", "created_at": now}


def claim_task(runtime_id: str, runtime_token: str, lease_seconds: int = 120) -> dict | None:
    runtime_id = str(runtime_id or "").strip()
    token_hash = hashlib.sha256(str(runtime_token or "").encode()).hexdigest()
    now = time.time()
    lease = max(15, min(int(lease_seconds), 600))
    with _db() as conn:
        runtime = conn.execute(
            "SELECT token_hash, status, expires_at FROM roaming_runtimes WHERE runtime_id=?",
            (runtime_id,),
        ).fetchone()
        if not runtime or not secrets.compare_digest(runtime["token_hash"], token_hash):
            raise PermissionError("runtime_authentication_failed")
        if runtime["status"] != "online" or runtime["expires_at"] <= now:
            raise PermissionError("runtime_offline")
        # Expired leases are returned to the queue so a restarted worker can recover.
        conn.execute("""
            UPDATE roaming_tasks SET status='queued', claimed_at=NULL, lease_until=NULL,
                updated_at=? WHERE runtime_id=? AND status='claimed' AND lease_until<=?
        """, (now, runtime_id, now))
        row = conn.execute(
            "SELECT * FROM roaming_tasks WHERE runtime_id=? AND status='queued' ORDER BY created_at LIMIT 1",
            (runtime_id,),
        ).fetchone()
        if not row:
            return None
        conn.execute("""
            UPDATE roaming_tasks SET status='claimed', claimed_at=?, lease_until=?,
                attempts=attempts+1, updated_at=? WHERE task_id=? AND status='queued'
        """, (now, now + lease, now, row["task_id"]))
        claimed = conn.execute("SELECT * FROM roaming_tasks WHERE task_id=?", (row["task_id"],)).fetchone()
    return _task_public(claimed)


def complete_task(runtime_id: str, runtime_token: str, task_id: str, result: dict, failed: bool = False) -> dict:
    runtime_id = str(runtime_id or "").strip()
    token_hash = hashlib.sha256(str(runtime_token or "").encode()).hexdigest()
    if not isinstance(result, dict):
        raise ValueError("task_result_must_be_object")
    encoded = json.dumps(result, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > 64000:
        raise ValueError("task_result_too_large")
    now = time.time()
    with _db() as conn:
        runtime = conn.execute("SELECT token_hash FROM roaming_runtimes WHERE runtime_id=?", (runtime_id,)).fetchone()
        if not runtime or not secrets.compare_digest(runtime["token_hash"], token_hash):
            raise PermissionError("runtime_authentication_failed")
        updated = conn.execute("""
            UPDATE roaming_tasks SET status=?, result=?, completed_at=?, updated_at=?,
                lease_until=NULL WHERE task_id=? AND runtime_id=? AND status='claimed'
        """, ("failed" if failed else "completed", encoded, now, now, str(task_id), runtime_id))
        if updated.rowcount != 1:
            raise LookupError("claimed_task_not_found")
        row = conn.execute("SELECT * FROM roaming_tasks WHERE task_id=?", (str(task_id),)).fetchone()
    return _task_public(row)


def _task_public(row) -> dict:
    return {
        "task_id": row["task_id"], "runtime_id": row["runtime_id"],
        "task_type": row["task_type"], "payload": json.loads(row["payload"]),
        "workspace_id": row["workspace_id"], "status": row["status"],
        "result": json.loads(row["result"]) if row["result"] else None,
        "attempts": row["attempts"], "created_at": row["created_at"],
        "updated_at": row["updated_at"], "completed_at": row["completed_at"],
    }
