"""Persistent local store for XParallel's Parallel Verse.

This is a storage boundary and local-development implementation, not a claim that
serverless /tmp storage is durable. For deployed persistence, configure XP_VERSE_DB
to a durable mounted volume or replace this adapter with managed PostgreSQL.
"""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

IS_SERVERLESS = os.getenv("VERCEL") == "1" or bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
DEFAULT_DB = os.getenv(
    "XP_VERSE_DB",
    "/tmp/.xparallel/parallel_verse.db" if IS_SERVERLESS else ".xparallel/parallel_verse.db",
)
_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB
    if path != ":memory:":
        Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS verse_agents (
            agent_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            kind TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_verse_agents_workspace
            ON verse_agents(workspace_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS verse_spaces (
            space_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_verse_spaces_workspace
            ON verse_spaces(workspace_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS verse_events (
            event_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            space_id TEXT,
            agent_id TEXT,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_verse_events_workspace
            ON verse_events(workspace_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS verse_tasks (
            task_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            space_id TEXT,
            created_by TEXT,
            assigned_to TEXT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            result_json TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_verse_tasks_workspace
            ON verse_tasks(workspace_id, created_at DESC);
    """)
    conn.commit()
    return conn


def _workspace(value: str) -> str:
    workspace = str(value or "default").strip()
    if not workspace or len(workspace) > 200:
        raise ValueError("invalid_workspace_id")
    return workspace


def _json(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_json_value") from exc


def _agent(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["metadata"] = json.loads(item.pop("metadata_json"))
    return item


def _space(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def _event(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["payload"] = json.loads(item.pop("payload_json"))
    return item


def _task(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    raw = item.pop("result_json")
    item["result"] = json.loads(raw) if raw else None
    return item


def register_agent(workspace_id: str, name: str, kind: str = "general",
                   metadata: dict[str, Any] | None = None,
                   db_path: str | None = None) -> dict[str, Any]:
    workspace = _workspace(workspace_id)
    name, kind = str(name).strip(), str(kind).strip()
    if not name or len(name) > 160:
        raise ValueError("agent_name_required_or_too_long")
    if not kind or len(kind) > 80:
        raise ValueError("invalid_agent_kind")
    if metadata is not None and not isinstance(metadata, dict):
        raise ValueError("metadata_must_be_object")
    now, agent_id = _now(), "agt_" + uuid.uuid4().hex
    with _LOCK, closing(_connect(db_path)) as conn:
        conn.execute(
            "INSERT INTO verse_agents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (agent_id, workspace, name, kind, "active", _json(metadata or {}), now, now),
        )
        conn.execute(
            "INSERT INTO verse_events VALUES (?, ?, NULL, ?, ?, ?, ?)",
            ("evt_" + uuid.uuid4().hex, workspace, agent_id, "agent.registered",
             _json({"name": name, "kind": kind}), now),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM verse_agents WHERE agent_id=?", (agent_id,)).fetchone()
    return _agent(row)


def list_agents(workspace_id: str, limit: int = 50,
                db_path: str | None = None) -> list[dict[str, Any]]:
    workspace = _workspace(workspace_id)
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid_limit") from exc
    with _LOCK, closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM verse_agents WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace, limit),
        ).fetchall()
    return [_agent(row) for row in rows]


def create_space(workspace_id: str, name: str, description: str = "",
                 db_path: str | None = None) -> dict[str, Any]:
    workspace, name = _workspace(workspace_id), str(name).strip()
    if not name or len(name) > 160:
        raise ValueError("space_name_required_or_too_long")
    if len(str(description)) > 4000:
        raise ValueError("space_description_too_long")
    space = {"space_id": "spc_" + uuid.uuid4().hex, "workspace_id": workspace,
             "name": name, "description": str(description), "created_at": _now()}
    with _LOCK, closing(_connect(db_path)) as conn:
        conn.execute("INSERT INTO verse_spaces VALUES (?, ?, ?, ?, ?)",
                     tuple(space.values()))
        conn.execute(
            "INSERT INTO verse_events VALUES (?, ?, ?, NULL, ?, ?, ?)",
            ("evt_" + uuid.uuid4().hex, workspace, space["space_id"], "space.created",
             _json({"name": name}), space["created_at"]),
        )
        conn.commit()
    return space


def list_spaces(workspace_id: str, limit: int = 50,
                db_path: str | None = None) -> list[dict[str, Any]]:
    workspace = _workspace(workspace_id)
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid_limit") from exc
    with _LOCK, closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM verse_spaces WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace, limit),
        ).fetchall()
    return [_space(row) for row in rows]


def record_event(workspace_id: str, event_type: str, payload: dict[str, Any] | None = None,
                 space_id: str | None = None, agent_id: str | None = None,
                 db_path: str | None = None) -> dict[str, Any]:
    workspace, event_type = _workspace(workspace_id), str(event_type).strip()
    if not event_type or len(event_type) > 120:
        raise ValueError("event_type_required_or_too_long")
    if payload is not None and not isinstance(payload, dict):
        raise ValueError("payload_must_be_object")
    event = {"event_id": "evt_" + uuid.uuid4().hex, "workspace_id": workspace,
             "space_id": space_id, "agent_id": agent_id, "event_type": event_type,
             "payload": payload or {}, "created_at": _now()}
    with _LOCK, closing(_connect(db_path)) as conn:
        for table, key, value in (("verse_spaces", "space_id", space_id),
                                  ("verse_agents", "agent_id", agent_id)):
            if value:
                row = conn.execute(
                    f"SELECT 1 FROM {table} WHERE {key}=? AND workspace_id=?",
                    (value, workspace),
                ).fetchone()
                if not row:
                    raise ValueError(f"{key}_not_found_in_workspace")
        conn.execute(
            "INSERT INTO verse_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            (event["event_id"], workspace, space_id, agent_id, event_type,
             _json(event["payload"]), event["created_at"]),
        )
        conn.commit()
    return event


def list_events(workspace_id: str, limit: int = 50,
                db_path: str | None = None) -> list[dict[str, Any]]:
    workspace = _workspace(workspace_id)
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid_limit") from exc
    with _LOCK, closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM verse_events WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace, limit),
        ).fetchall()
    return [_event(row) for row in rows]


def create_task(workspace_id: str, title: str, description: str = "",
                space_id: str | None = None, created_by: str | None = None,
                assigned_to: str | None = None, db_path: str | None = None) -> dict[str, Any]:
    workspace, title = _workspace(workspace_id), str(title).strip()
    if not title or len(title) > 240:
        raise ValueError("task_title_required_or_too_long")
    if len(str(description)) > 8000:
        raise ValueError("task_description_too_long")
    now, task_id = _now(), "tsk_" + uuid.uuid4().hex
    with _LOCK, closing(_connect(db_path)) as conn:
        for table, key, value in (("verse_spaces", "space_id", space_id),
                                  ("verse_agents", "agent_id", created_by),
                                  ("verse_agents", "agent_id", assigned_to)):
            if value and not conn.execute(
                f"SELECT 1 FROM {table} WHERE {key}=? AND workspace_id=?",
                (value, workspace),
            ).fetchone():
                raise ValueError(f"{key}_not_found_in_workspace")
        task = {"task_id": task_id, "workspace_id": workspace, "space_id": space_id,
                "created_by": created_by, "assigned_to": assigned_to, "title": title,
                "description": str(description), "status": "open", "result": None,
                "created_at": now, "updated_at": now}
        conn.execute(
            "INSERT INTO verse_tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)",
            (task_id, workspace, space_id, created_by, assigned_to, title,
             str(description), "open", now, now),
        )
        conn.execute(
            "INSERT INTO verse_events VALUES (?, ?, ?, ?, ?, ?, ?)",
            ("evt_" + uuid.uuid4().hex, workspace, space_id, created_by,
             "task.created", _json({"task_id": task_id, "title": title}), now),
        )
        conn.commit()
    return task


def list_tasks(workspace_id: str, limit: int = 50,
               db_path: str | None = None) -> list[dict[str, Any]]:
    workspace = _workspace(workspace_id)
    try:
        limit = max(1, min(int(limit), 100))
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid_limit") from exc
    with _LOCK, closing(_connect(db_path)) as conn:
        rows = conn.execute(
            "SELECT * FROM verse_tasks WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace, limit),
        ).fetchall()
    return [_task(row) for row in rows]
