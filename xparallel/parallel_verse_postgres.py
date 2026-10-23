"""PostgreSQL storage adapter for Parallel Verse; opt-in via XP_VERSE_BACKEND=postgres.

Requires psycopg 3 and XP_VERSE_DATABASE_URL. This module never creates cloud
resources. Apply migrations explicitly before switching a deployed service.
"""
from __future__ import annotations
import json, os, uuid
from datetime import datetime, timezone

def _now(): return datetime.now(timezone.utc)
def _workspace(v):
    value = str(v or "default").strip()
    if not value or len(value) > 200: raise ValueError("invalid_workspace_id")
    return value
def _connect():
    url = os.getenv("XP_VERSE_DATABASE_URL", "").strip()
    if not url: raise RuntimeError("xp_verse_database_url_required")
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("psycopg_required_for_postgres_backend") from exc
    return psycopg.connect(url, row_factory=dict_row, connect_timeout=5)
def _limit(v):
    try: return max(1, min(int(v), 100))
    except (ValueError, TypeError) as exc: raise ValueError("invalid_limit") from exc
def _row(row):
    if row is None: return None
    return {k:(v.isoformat() if hasattr(v,"isoformat") else v) for k,v in dict(row).items()}
def _exists(cur, table, key, value, workspace):
    if value and not cur.execute(f"SELECT 1 FROM {table} WHERE {key}=%s AND workspace_id=%s", (value,workspace)).fetchone():
        raise ValueError(f"{key}_not_found_in_workspace")
def register_agent(workspace_id,name,kind="general",metadata=None,db_path=None):
    w=_workspace(workspace_id); name=str(name).strip(); kind=str(kind).strip()
    if not name or len(name)>160: raise ValueError("agent_name_required_or_too_long")
    if not kind or len(kind)>80: raise ValueError("invalid_agent_kind")
    if metadata is not None and not isinstance(metadata,dict): raise ValueError("metadata_must_be_object")
    now=_now(); aid="agt_"+uuid.uuid4().hex
    with _connect() as c, c.cursor() as q:
        q.execute("INSERT INTO verse_agents VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s,%s)",(aid,w,name,kind,"active",json.dumps(metadata or {}),now,now))
        q.execute("INSERT INTO verse_events VALUES (%s,%s,NULL,%s,%s,%s::jsonb,%s)",("evt_"+uuid.uuid4().hex,w,aid,"agent.registered",json.dumps({"name":name,"kind":kind}),now))
        row=q.execute("SELECT * FROM verse_agents WHERE agent_id=%s",(aid,)).fetchone()
    out=_row(row); out["metadata"]=out.pop("metadata_json"); return out
def list_agents(workspace_id,limit=50,db_path=None):
    with _connect() as c, c.cursor() as q: rows=q.execute("SELECT * FROM verse_agents WHERE workspace_id=%s ORDER BY created_at DESC LIMIT %s",(_workspace(workspace_id),_limit(limit))).fetchall()
    return [{**_row(r),"metadata":r["metadata_json"]} for r in rows]
def create_space(workspace_id,name,description="",db_path=None):
    w=_workspace(workspace_id); name=str(name).strip(); description=str(description)
    if not name or len(name)>160: raise ValueError("space_name_required_or_too_long")
    if len(description)>4000: raise ValueError("space_description_too_long")
    now=_now(); s={"space_id":"spc_"+uuid.uuid4().hex,"workspace_id":w,"name":name,"description":description,"created_at":now}
    with _connect() as c, c.cursor() as q:
        q.execute("INSERT INTO verse_spaces VALUES (%s,%s,%s,%s,%s)",tuple(s.values()))
        q.execute("INSERT INTO verse_events VALUES (%s,%s,%s,NULL,%s,%s::jsonb,%s)",("evt_"+uuid.uuid4().hex,w,s["space_id"],"space.created",json.dumps({"name":name}),now))
    return _row(s)
def list_spaces(workspace_id,limit=50,db_path=None):
    with _connect() as c, c.cursor() as q: rows=q.execute("SELECT * FROM verse_spaces WHERE workspace_id=%s ORDER BY created_at DESC LIMIT %s",(_workspace(workspace_id),_limit(limit))).fetchall()
    return [_row(r) for r in rows]
def record_event(workspace_id,event_type,payload=None,space_id=None,agent_id=None,db_path=None):
    w=_workspace(workspace_id); typ=str(event_type).strip()
    if not typ or len(typ)>120: raise ValueError("event_type_required_or_too_long")
    if payload is not None and not isinstance(payload,dict): raise ValueError("payload_must_be_object")
    now=_now(); ev={"event_id":"evt_"+uuid.uuid4().hex,"workspace_id":w,"space_id":space_id,"agent_id":agent_id,"event_type":typ,"payload":payload or {},"created_at":now}
    with _connect() as c, c.cursor() as q:
        _exists(q,"verse_spaces","space_id",space_id,w); _exists(q,"verse_agents","agent_id",agent_id,w)
        q.execute("INSERT INTO verse_events VALUES (%s,%s,%s,%s,%s,%s::jsonb,%s)",(ev["event_id"],w,space_id,agent_id,typ,json.dumps(ev["payload"]),now))
    return _row(ev)
def list_events(workspace_id,limit=50,db_path=None):
    with _connect() as c, c.cursor() as q: rows=q.execute("SELECT * FROM verse_events WHERE workspace_id=%s ORDER BY created_at DESC LIMIT %s",(_workspace(workspace_id),_limit(limit))).fetchall()
    return [{**_row(r),"payload":r["payload_json"]} for r in rows]
def create_task(workspace_id,title,description="",space_id=None,created_by=None,assigned_to=None,db_path=None):
    w=_workspace(workspace_id); title=str(title).strip(); description=str(description)
    if not title or len(title)>240: raise ValueError("task_title_required_or_too_long")
    if len(description)>8000: raise ValueError("task_description_too_long")
    now=_now(); tid="tsk_"+uuid.uuid4().hex
    with _connect() as c, c.cursor() as q:
        _exists(q,"verse_spaces","space_id",space_id,w); _exists(q,"verse_agents","agent_id",created_by,w); _exists(q,"verse_agents","agent_id",assigned_to,w)
        q.execute("INSERT INTO verse_tasks VALUES (%s,%s,%s,%s,%s,%s,%s,%s,NULL,%s,%s)",(tid,w,space_id,created_by,assigned_to,title,description,"open",now,now))
        q.execute("INSERT INTO verse_events VALUES (%s,%s,%s,%s,%s,%s,%s)",("evt_"+uuid.uuid4().hex,w,space_id,created_by,"task.created",json.dumps({"task_id":tid,"title":title}),now))
    return {"task_id":tid,"workspace_id":w,"space_id":space_id,"created_by":created_by,"assigned_to":assigned_to,"title":title,"description":description,"status":"open","result":None,"created_at":now.isoformat(),"updated_at":now.isoformat()}
def list_tasks(workspace_id,limit=50,db_path=None):
    with _connect() as c, c.cursor() as q: rows=q.execute("SELECT * FROM verse_tasks WHERE workspace_id=%s ORDER BY created_at DESC LIMIT %s",(_workspace(workspace_id),_limit(limit))).fetchall()
    return [{**_row(r),"result":r["result_json"]} for r in rows]
