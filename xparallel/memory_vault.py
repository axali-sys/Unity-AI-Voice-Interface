"""XParallel Memory Vault: compact searchable memory with content-addressed deduplication.

This V1 stores recoverable source text in SQLite and indexes it for keyword retrieval.
It deliberately does not treat AI summaries/embeddings as a replacement for source data.
Set XP_MEMORY_DB to a persistent writable path in production.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

DEFAULT_DB = os.getenv("XP_MEMORY_DB", "xparallel_memory.sqlite3")


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    if path != ":memory:":
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_items (
            id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            tags_json TEXT NOT NULL DEFAULT '[]',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(workspace_id, content_hash)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memory_workspace ON memory_items(workspace_id, updated_at)")
    return conn


def save_memory(content: str, workspace_id: str = "default", summary: str = "",
                tags: list[str] | None = None, db_path: str | None = None) -> dict[str, Any]:
    """Save recoverable text; identical content in one workspace reuses its record."""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("content_required")
    if len(content.encode("utf-8")) > 2_000_000:
        raise ValueError("content_too_large")
    workspace = str(workspace_id).strip()[:200] or "default"
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    now = time.time()
    tags_json = json.dumps([str(t)[:100] for t in (tags or [])[:50]])
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM memory_items WHERE workspace_id=? AND content_hash=?",
            (workspace, digest),
        ).fetchone()
        if row:
            conn.execute("UPDATE memory_items SET summary=?, tags_json=?, updated_at=? WHERE id=?",
                         (str(summary)[:4000], tags_json, now, row["id"]))
            item_id, created = row["id"], False
        else:
            item_id, created = uuid.uuid4().hex, True
            conn.execute(
                "INSERT INTO memory_items(id,workspace_id,content_hash,content,summary,tags_json,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (item_id, workspace, digest, content, str(summary)[:4000], tags_json, now, now),
            )
        return {"id": item_id, "workspace_id": workspace, "content_hash": digest,
                "created": created, "source_preserved": True, "updated_at": now}


def search_memories(query: str, workspace_id: str = "default", limit: int = 10,
                    db_path: str | None = None) -> list[dict[str, Any]]:
    """Simple local lexical retrieval for V1; semantic embeddings can be added later."""
    terms = [t.casefold() for t in str(query).split() if len(t) > 1]
    if not terms:
        return []
    limit = max(1, min(int(limit), 50))
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, workspace_id, content_hash, content, summary, tags_json, updated_at FROM memory_items WHERE workspace_id=? ORDER BY updated_at DESC LIMIT 1000",
            (str(workspace_id).strip() or "default",),
        ).fetchall()
    scored = []
    for row in rows:
        haystack = (row["content"] + " " + row["summary"] + " " + row["tags_json"]).casefold()
        score = sum(haystack.count(term) for term in terms)
        if score:
            item = dict(row)
            item["tags"] = json.loads(item.pop("tags_json"))
            item["score"] = score
            scored.append(item)
    scored.sort(key=lambda x: (x["score"], x["updated_at"]), reverse=True)
    return scored[:limit]


def list_memories(workspace_id: str = "default", limit: int = 50,
                  db_path: str | None = None) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT id, workspace_id, content_hash, content, summary, tags_json, created_at, updated_at FROM memory_items WHERE workspace_id=? ORDER BY updated_at DESC LIMIT ?",
            (str(workspace_id).strip() or "default", limit),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["tags"] = json.loads(item.pop("tags_json"))
        result.append(item)
    return result


def forget_memory(memory_id: str, workspace_id: str = "default",
                  db_path: str | None = None) -> bool:
    """Delete one memory record; backups and external replicas are not purged by this function."""
    with _connect(db_path) as conn:
        cursor = conn.execute("DELETE FROM memory_items WHERE id=? AND workspace_id=?",
                              (str(memory_id), str(workspace_id).strip() or "default"))
        return cursor.rowcount > 0
