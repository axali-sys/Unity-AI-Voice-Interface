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
    return conn


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
    with _connect() as conn:
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
    with _connect() as conn:
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
    with _connect() as conn:
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
