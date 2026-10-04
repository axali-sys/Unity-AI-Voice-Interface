"""XParallel persistence boundary.

Uses SQLite locally and as a safe default. Production deployments can replace
this repository with a managed SQL adapter without changing API semantics.
"""
from __future__ import annotations
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_PATH = os.getenv("XP_DB_PATH", ".xparallel/xparallel.db")

class SolutionRepository:
    def __init__(self, path: str | None = None):
        self.path = path or DEFAULT_PATH
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.execute("""CREATE TABLE IF NOT EXISTS solutions (
            node_id TEXT PRIMARY KEY,
            workspace_id TEXT NOT NULL,
            status TEXT NOT NULL,
            tags TEXT NOT NULL,
            solution TEXT NOT NULL,
            created_at TEXT NOT NULL,
            graph_fingerprint TEXT NOT NULL
        )""")
        self._db.commit()

    def put(self, workspace_id: str, node: dict[str, Any]) -> dict[str, Any]:
        self._db.execute(
            "INSERT OR REPLACE INTO solutions VALUES (?, ?, ?, ?, ?, ?, ?)",
            (node["node_id"], workspace_id, node["status"], json.dumps(node["tags"]),
             json.dumps(node["solution"], sort_keys=True), node["created_at"], node["graph_fingerprint"])
        )
        self._db.commit()
        return node

    def get(self, workspace_id: str, node_id: str) -> dict[str, Any] | None:
        row = self._db.execute(
            "SELECT node_id,status,tags,solution,created_at,graph_fingerprint FROM solutions WHERE workspace_id=? AND node_id=?",
            (workspace_id, node_id)
        ).fetchone()
        if not row:
            return None
        return {"node_id":row[0],"status":row[1],"tags":json.loads(row[2]),
                "solution":json.loads(row[3]),"created_at":row[4],"graph_fingerprint":row[5]}

    def list(self, workspace_id: str, limit: int = 50) -> list[dict[str, Any]]:
        rows = self._db.execute(
            "SELECT node_id,status,tags,solution,created_at,graph_fingerprint FROM solutions WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",
            (workspace_id, max(1, min(limit, 200)))
        ).fetchall()
        return [{"node_id":r[0],"status":r[1],"tags":json.loads(r[2]),"solution":json.loads(r[3]),
                 "created_at":r[4],"graph_fingerprint":r[5]} for r in rows]

    def close(self) -> None:
        self._db.close()

REPOSITORY = SolutionRepository()
