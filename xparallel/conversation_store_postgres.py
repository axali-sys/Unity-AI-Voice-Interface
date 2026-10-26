"""Opt-in PostgreSQL conversation history adapter.

Selected only with XP_CONVERSATION_BACKEND=postgres. SQLite remains the default.
Requires migrations/parallel_verse/0003_conversations.sql to be applied explicitly.
"""
from __future__ import annotations
import json, os, time
from pathlib import Path
from typing import Any

def _connect():
    url = os.getenv("XP_VERSE_DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError("xp_verse_database_url_required")
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("psycopg_required_for_postgres_backend") from exc
    return psycopg.connect(url, row_factory=dict_row, connect_timeout=5)

def _messages(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list) or len(value) > 200:
        raise ValueError("invalid_messages")
    result=[]; total=0
    for item in value:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
            raise ValueError("invalid_message")
        content=item["content"].strip()
        if not content or len(content)>24000:
            raise ValueError("invalid_message_content")
        total += len(content)
        if total > 500_000:
            raise ValueError("conversation_too_large")
        result.append({"role":item["role"],"content":content})
    return result

def save_conversation(conversation_id: str, workspace_id: str, title: str, messages: Any) -> dict[str, Any]:
    conversation_id=str(conversation_id or "").strip()[:100]
    workspace=str(workspace_id or "default").strip()[:64] or "default"
    if not conversation_id: raise ValueError("conversation_id_required")
    clean=_messages(messages)
    safe_title=str(title or "New chat").strip()[:200] or "New chat"
    now=time.time()
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("""INSERT INTO axaliai_conversations
          (conversation_id,workspace_id,title,messages_json,created_at,updated_at)
          VALUES (%s,%s,%s,%s::jsonb,%s,%s)
          ON CONFLICT(workspace_id,conversation_id) DO UPDATE SET
          title=excluded.title,messages_json=excluded.messages_json,updated_at=excluded.updated_at""",
          (conversation_id,workspace,safe_title,json.dumps(clean,ensure_ascii=False),now,now))
    return {"conversation_id":conversation_id,"workspace_id":workspace,"title":safe_title,
            "message_count":len(clean),"updated_at":now}

def get_conversation(conversation_id: str, workspace_id: str) -> dict[str, Any] | None:
    with _connect() as conn, conn.cursor() as cur:
        row=cur.execute("""SELECT * FROM axaliai_conversations
          WHERE conversation_id=%s AND workspace_id=%s""",
          (str(conversation_id),str(workspace_id or "default"))).fetchone()
    if not row: return None
    return {"conversation_id":row["conversation_id"],"workspace_id":row["workspace_id"],
            "title":row["title"],"messages":row["messages_json"],
            "created_at":row["created_at"],"updated_at":row["updated_at"]}

def list_conversations(workspace_id: str, limit: int = 50) -> list[dict[str, Any]]:
    try: limit=max(1,min(int(limit),100))
    except (ValueError,TypeError) as exc: raise ValueError("invalid_limit") from exc
    with _connect() as conn, conn.cursor() as cur:
        rows=cur.execute("""SELECT conversation_id,workspace_id,title,messages_json,created_at,updated_at
          FROM axaliai_conversations WHERE workspace_id=%s ORDER BY updated_at DESC LIMIT %s""",
          (str(workspace_id or "default"),limit)).fetchall()
    return [{"conversation_id":r["conversation_id"],"workspace_id":r["workspace_id"],
             "title":r["title"],"message_count":len(r["messages_json"]),
             "created_at":r["created_at"],"updated_at":r["updated_at"]} for r in rows]

def delete_conversation(conversation_id: str, workspace_id: str) -> bool:
    with _connect() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM axaliai_conversations WHERE conversation_id=%s AND workspace_id=%s",
                    (str(conversation_id),str(workspace_id or "default")))
        return cur.rowcount > 0
