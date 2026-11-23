"""Workspace-scoped immutable memory snapshots and integrity verification.

Snapshots share the configured SQLite database with the memory vault. The SHA-256
manifest detects corruption; it is not a cryptographic signature or proof that the
snapshot was created by a trusted actor. Production trust requires authenticated
snapshot signing and durable storage outside ephemeral serverless filesystems.
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from typing import Any

from .memory_vault import _connect


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _ensure_schema(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_snapshots (
            snapshot_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            item_count INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'available'
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_snapshots_workspace "
                 "ON memory_snapshots(workspace_id, created_at)")


def create_snapshot(workspace_id: str = "default",
                   db_path: str | None = None) -> dict[str, Any]:
    workspace = str(workspace_id or "default").strip()[:200] or "default"
    with _connect(db_path) as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            "SELECT id, workspace_id, content_hash, content, summary, tags_json, "
            "created_at, updated_at FROM memory_items WHERE workspace_id=? "
            "ORDER BY id", (workspace,)
        ).fetchall()
        items = [{
            "id": row["id"], "workspace_id": row["workspace_id"],
            "content_hash": row["content_hash"], "content": row["content"],
            "summary": row["summary"], "tags": json.loads(row["tags_json"]),
            "created_at": row["created_at"], "updated_at": row["updated_at"],
        } for row in rows]
        payload = {"format": "xparallel-memory-snapshot-v1",
                   "workspace_id": workspace, "items": items}
        payload_json = _canonical(payload).decode("utf-8")
        digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        snapshot_id, now = uuid.uuid4().hex, time.time()
        conn.execute(
            "INSERT INTO memory_snapshots(snapshot_id,workspace_id,created_at,"
            "item_count,payload_json,payload_sha256,status) VALUES(?,?,?,?,?,?,?)",
            (snapshot_id, workspace, now, len(items), payload_json, digest, "available")
        )
        return {"snapshot_id": snapshot_id, "workspace_id": workspace,
                "created_at": now, "item_count": len(items), "sha256": digest}


def verify_snapshot(snapshot_id: str, workspace_id: str,
                    db_path: str | None = None) -> dict[str, Any]:
    workspace = str(workspace_id or "default").strip() or "default"
    with _connect(db_path) as conn:
        _ensure_schema(conn)
        row = conn.execute(
            "SELECT * FROM memory_snapshots WHERE snapshot_id=? AND workspace_id=?",
            (str(snapshot_id), workspace)
        ).fetchone()
    if not row:
        return {"valid": False, "reason": "snapshot_not_found"}
    raw = row["payload_json"]
    actual = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    if actual != row["payload_sha256"]:
        return {"valid": False, "reason": "integrity_mismatch"}
    try:
        payload = json.loads(raw)
        if payload.get("format") != "xparallel-memory-snapshot-v1":
            raise ValueError("format")
        if payload.get("workspace_id") != workspace:
            raise ValueError("workspace")
        items = payload.get("items")
        if not isinstance(items, list) or len(items) != row["item_count"]:
            raise ValueError("count")
        for item in items:
            if item.get("workspace_id") != workspace:
                raise ValueError("owner")
            content = item.get("content")
            expected = item.get("content_hash")
            if not isinstance(content, str) or hashlib.sha256(content.encode("utf-8")).hexdigest() != expected:
                raise ValueError("content_hash")
            if not isinstance(item.get("tags"), list):
                raise ValueError("tags")
    except (ValueError, TypeError, AttributeError):
        return {"valid": False, "reason": "payload_schema_invalid"}
    return {"valid": True, "reason": "verified", "snapshot_id": str(snapshot_id),
            "workspace_id": workspace, "item_count": len(items), "sha256": actual,
            "payload": payload}


def list_snapshots(workspace_id: str = "default", limit: int = 20,
                   db_path: str | None = None) -> list[dict[str, Any]]:
    workspace = str(workspace_id or "default").strip() or "default"
    limit = max(1, min(int(limit), 100))
    with _connect(db_path) as conn:
        _ensure_schema(conn)
        rows = conn.execute(
            "SELECT snapshot_id,workspace_id,created_at,item_count,payload_sha256,status "
            "FROM memory_snapshots WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace, limit)
        ).fetchall()
    return [dict(row) for row in rows]
