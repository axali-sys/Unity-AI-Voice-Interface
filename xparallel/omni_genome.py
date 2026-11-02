from __future__ import annotations
import json, os, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone

DB_ENV='OMNI_DB'
def now(): return datetime.now(timezone.utc).isoformat()
def uid(prefix): return prefix+'-'+uuid.uuid4().hex
@contextmanager
def db():
 c=sqlite3.connect(os.getenv(DB_ENV,'oneai_omni.sqlite3'),timeout=10); c.row_factory=sqlite3.Row; c.execute('PRAGMA foreign_keys=ON')
 try:
  c.executescript('''CREATE TABLE IF NOT EXISTS omni_records(id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL,record_type TEXT NOT NULL,subject TEXT NOT NULL,content TEXT NOT NULL,context_json TEXT NOT NULL,origin TEXT NOT NULL,actor_id TEXT,status TEXT NOT NULL,verification_status TEXT NOT NULL DEFAULT 'unverified',current_version INTEGER NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL); CREATE INDEX IF NOT EXISTS idx_omni_workspace ON omni_records(workspace_id,updated_at); CREATE TABLE IF NOT EXISTS omni_sources(id TEXT PRIMARY KEY,record_id TEXT NOT NULL,workspace_id TEXT NOT NULL,source_type TEXT NOT NULL,source_ref TEXT,description TEXT,created_at TEXT NOT NULL,FOREIGN KEY(record_id) REFERENCES omni_records(id)); CREATE TABLE IF NOT EXISTS omni_versions(record_id TEXT NOT NULL,version INTEGER NOT NULL,workspace_id TEXT NOT NULL,subject TEXT NOT NULL,content TEXT NOT NULL,context_json TEXT NOT NULL,actor_id TEXT,created_at TEXT NOT NULL,PRIMARY KEY(record_id,version),FOREIGN KEY(record_id) REFERENCES omni_records(id)); CREATE TABLE IF NOT EXISTS omni_verifications(id TEXT PRIMARY KEY,record_id TEXT NOT NULL,workspace_id TEXT NOT NULL,method TEXT NOT NULL,actor_id TEXT NOT NULL,result TEXT NOT NULL,evidence_json TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(record_id) REFERENCES omni_records(id)); CREATE TABLE IF NOT EXISTS omni_events(id TEXT PRIMARY KEY,event_type TEXT NOT NULL,workspace_id TEXT NOT NULL,entity_id TEXT NOT NULL,actor_id TEXT,payload_json TEXT NOT NULL,created_at TEXT NOT NULL);''')
  with c: yield c
 finally: c.close()
def _ws(w):
 w=str(w or '').strip()
 if not w or len(w)>128: raise ValueError('workspace_id_required')
 return w
def _event(c,typ,w,e,a,p): c.execute('INSERT INTO omni_events VALUES(?,?,?,?,?,?,?)',(uid('EVT'),typ,w,e,a,json.dumps(p,sort_keys=True),now()))
def _item(r):
 if not r:return None
 d=dict(r); d['context']=json.loads(d.pop('context_json')); return d
def create_record(workspace_id,record_type,subject,content,*,context=None,origin='user',actor_id=None,source=None):
 w=_ws(workspace_id)
 if not all(str(x or '').strip() for x in (record_type,subject,content)): raise ValueError('record_type_subject_content_required')
 if not isinstance(context or {},dict): raise ValueError('context_must_be_object')
 if origin not in {'user','file','url','conversation','model','system','external'}: raise ValueError('origin_invalid')
 rid,t=uid('OMNI-K'),now(); cj=json.dumps(context or {},sort_keys=True)
 with db() as c:
  c.execute('INSERT INTO omni_records VALUES(?,?,?,?,?,?,?,?,?,?,1,?,?)',(rid,w,record_type,subject,content,cj,origin,actor_id,'received','unverified',t,t))
  c.execute('INSERT INTO omni_versions VALUES(?,?,?,?,?,?,?,?)',(rid,1,w,subject,content,cj,actor_id,t))
  if source:
   if not source.get('source_type'): raise ValueError('source_type_required')
   c.execute('INSERT INTO omni_sources VALUES(?,?,?,?,?,?,?)',(uid('OMNI-S'),rid,w,source['source_type'],source.get('source_ref'),source.get('description'),t))
  _event(c,'knowledge.record.created',w,rid,actor_id,{'origin':origin,'status':'received'})
 return get_record(rid,w)
def get_record(record_id,workspace_id):
 w=_ws(workspace_id)
 with db() as c:
  r=c.execute('SELECT * FROM omni_records WHERE id=? AND workspace_id=?',(record_id,w)).fetchone()
  if not r:return None
  d=_item(r); d['sources']=[dict(x) for x in c.execute('SELECT id,source_type,source_ref,description,created_at FROM omni_sources WHERE record_id=? AND workspace_id=?',(record_id,w))]; return d
def update_record(record_id,workspace_id,*,subject,content,context=None,actor_id=None):
 w=_ws(workspace_id)
 if not subject or not content or not isinstance(context or {},dict): raise ValueError('valid_subject_content_context_required')
 t,cj=now(),json.dumps(context or {},sort_keys=True)
 with db() as c:
  r=c.execute('SELECT current_version FROM omni_records WHERE id=? AND workspace_id=?',(record_id,w)).fetchone()
  if not r:return None
  v=r['current_version']+1
  c.execute('INSERT INTO omni_versions VALUES(?,?,?,?,?,?,?,?)',(record_id,v,w,subject,content,cj,actor_id,t))
  c.execute("UPDATE omni_records SET subject=?,content=?,context_json=?,current_version=?,status='received',verification_status='unverified',updated_at=? WHERE id=? AND workspace_id=?",(subject,content,cj,v,t,record_id,w))
  _event(c,'knowledge.record.versioned',w,record_id,actor_id,{'version':v})
 return get_record(record_id,w)
def list_versions(record_id,workspace_id):
 w=_ws(workspace_id)
 with db() as c: rows=c.execute('SELECT * FROM omni_versions WHERE record_id=? AND workspace_id=? ORDER BY version',(record_id,w)).fetchall()
 return [{**dict(r),'context':json.loads(r['context_json'])} for r in rows]
def search_records(workspace_id,query='',limit=20):
 w=_ws(workspace_id); limit=max(1,min(int(limit),100)); q=str(query or '')
 with db() as c: rows=c.execute("SELECT * FROM omni_records WHERE workspace_id=? AND (?='' OR subject LIKE ? OR content LIKE ?) ORDER BY updated_at DESC LIMIT ?",(w,q,'%'+q+'%','%'+q+'%',limit)).fetchall()
 return [_item(r) for r in rows]
def verify_record(record_id,workspace_id,*,method,actor_id,result,evidence):
 w=_ws(workspace_id)
 if not method or not actor_id or result not in {'verified','rejected','inconclusive'} or not evidence: raise ValueError('verification_method_actor_result_evidence_required')
 t,vid=now(),uid('OMNI-V')
 with db() as c:
  if not c.execute('SELECT 1 FROM omni_records WHERE id=? AND workspace_id=?',(record_id,w)).fetchone(): return None
  c.execute('INSERT INTO omni_verifications VALUES(?,?,?,?,?,?,?,?)',(vid,record_id,w,method,actor_id,result,json.dumps(evidence,sort_keys=True),t))
  status='verified' if result=='verified' else 'received'
  c.execute('UPDATE omni_records SET status=?,verification_status=?,updated_at=? WHERE id=? AND workspace_id=?',(status,result,t,record_id,w))
  _event(c,'knowledge.record.verification',w,record_id,actor_id,{'verification_id':vid,'result':result})
 return get_record(record_id,w)
