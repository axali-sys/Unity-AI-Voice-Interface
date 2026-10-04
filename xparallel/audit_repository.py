"""SQLite-backed audit repository for security-sensitive XParallel events."""
from __future__ import annotations
import json, os, sqlite3
from pathlib import Path
from typing import Any
from xparallel.audit import audit_event
DEFAULT_PATH=os.getenv("XP_DB_PATH",".xparallel/xparallel.db")
class AuditRepository:
    def __init__(self,path:str|None=None):
        self.path=path or DEFAULT_PATH
        if self.path != ":memory:": Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        self._db=sqlite3.connect(self.path)
        self._db.execute("CREATE TABLE IF NOT EXISTS audit_events (event_fingerprint TEXT PRIMARY KEY, action TEXT NOT NULL, workspace_id TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL, metadata TEXT NOT NULL, event TEXT NOT NULL)")
        self._db.commit()
    def record(self,action:str,workspace_id:str,actor:str="system",metadata:dict[str,Any]|None=None)->dict[str,Any]:
        event=audit_event(action,workspace_id,actor,metadata)
        self._db.execute("INSERT OR IGNORE INTO audit_events VALUES (?,?,?,?,?,?,?)",(event["event_fingerprint"],event["action"],event["workspace_id"],event["actor"],event["created_at"],json.dumps(event["metadata"],sort_keys=True),json.dumps(event,sort_keys=True)))
        self._db.commit(); return event
    def list(self,workspace_id:str,limit:int=100)->list[dict[str,Any]]:
        rows=self._db.execute("SELECT event FROM audit_events WHERE workspace_id=? ORDER BY created_at DESC LIMIT ?",(workspace_id,max(1,min(limit,500)))).fetchall()
        return [json.loads(row[0]) for row in rows]
AUDIT_REPOSITORY=AuditRepository()
