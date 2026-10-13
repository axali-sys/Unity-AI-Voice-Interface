"""SQLite-backed conversation history for Axaliai.

Conversation records are partitioned by workspace and stored alongside AI Memory
when XP_MEMORY_DB points to a persistent writable database. This is not a substitute
for per-user authentication: deployments must map authenticated users to distinct
workspace IDs before exposing the API to multiple users.
"""
from __future__ import annotations

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

def _db_path() -> str:
    return os.getenv("XP_MEMORY_DB", "xparallel_memory.sqlite3")

def _connect() -> sqlite3.Connection:
    path = _db_path()
    if path != ":memory:":
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS axaliai_conversations (
            conversation_id TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            title TEXT NOT NULL DEFAULT 'New chat',
            messages_json TEXT NOT NULL DEFAULT '[]',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            PRIMARY KEY (workspace_id, conversation_id)
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_axaliai_conversations_workspace ON axaliai_conversations(workspace_id, updated_at)")
    return conn

def _messages(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > 200:
        raise ValueError("invalid_messages")
    result = []
    total = 0
    for item in value:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
            raise ValueError("invalid_message")
        content = item["content"].strip()
        if not content or len(content) > 24000:
            raise ValueError("invalid_message_content")
        total += len(content)
        if total > 500_000:
            raise ValueError("conversation_too_large")
        result.append({"role": item["role"], "content": content})
    return result

def save_conversation(conversation_id: str, workspace_id: str, title: str, messages: Any) -> dict[str, Any]:
    conversation_id = str(conversation_id or "").strip()[:100]
    workspace = str(workspace_id or "default").strip()[:64] or "default"
    if not conversation_id:
        raise ValueError("conversation_id_required")
    clean = _messages(messages)
    safe_title = str(title or "New chat").strip()[:200] or "New chat"
    now = time.time()
    with _connect() as conn:
        conn.execute("""
            INSERT INTO axaliai_conversations(conversation_id, workspace_id, title, messages_json, created_at, updated_at)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(workspace_id, conversation_id) DO UPDATE SET
              title=excluded.title, messages_json=excluded.messages_json, updated_at=excluded.updated_at
        """, (conversation_id, workspace, safe_title, json.dumps(clean, ensure_ascii=False), now, now))
    return {"conversation_id": conversation_id, "workspace_id": workspace, "title": safe_title,
            "message_count": len(clean), "updated_at": now}

def get_conversation(conversation_id: str, workspace_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM axaliai_conversations WHERE conversation_id=? AND workspace_id=?",
                           (str(conversation_id), str(workspace_id or "default"))).fetchone()
    if not row:
        return None
    return {"conversation_id": row["conversation_id"], "workspace_id": row["workspace_id"],
            "title": row["title"], "messages": json.loads(row["messages_json"]),
            "created_at": row["created_at"], "updated_at": row["updated_at"]}

def list_conversations(workspace_id: str, limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 100))
    with _connect() as conn:
        rows = conn.execute("SELECT conversation_id, workspace_id, title, messages_json, created_at, updated_at "
                            "FROM axaliai_conversations WHERE workspace_id=? ORDER BY updated_at DESC LIMIT ?",
                            (str(workspace_id or "default"), limit)).fetchall()
    return [{"conversation_id": r["conversation_id"], "workspace_id": r["workspace_id"],
             "title": r["title"], "message_count": len(json.loads(r["messages_json"])),
             "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]

def delete_conversation(conversation_id: str, workspace_id: str) -> bool:
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM axaliai_conversations WHERE conversation_id=? AND workspace_id=?",
                              (str(conversation_id), str(workspace_id or "default")))
        return cursor.rowcount > 0
