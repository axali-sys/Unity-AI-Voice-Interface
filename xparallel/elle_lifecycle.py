from __future__ import annotations
import json,os,sqlite3,uuid
from contextlib import contextmanager
from datetime import datetime,timezone
STATES=('UNDERSTAND','REMEMBER','PLAN','COLLABORATE','RESEARCH','BUILD','VERIFY','APPROVE','EXECUTE','LEARN','COMPLETED','FAILED')
NEXT={'UNDERSTAND':{'REMEMBER','FAILED'},'REMEMBER':{'PLAN','FAILED'},'PLAN':{'COLLABORATE','RESEARCH','BUILD','FAILED'},'COLLABORATE':{'RESEARCH','BUILD','FAILED'},'RESEARCH':{'BUILD','VERIFY','FAILED'},'BUILD':{'VERIFY','FAILED'},'VERIFY':{'APPROVE','LEARN','FAILED'},'APPROVE':{'EXECUTE','LEARN','FAILED'},'EXECUTE':{'VERIFY','LEARN','FAILED'},'LEARN':{'COMPLETED','FAILED'},'COMPLETED':set(),'FAILED':set()}
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return 'ELLE-T-'+uuid.uuid4().hex
@contextmanager
def db():
 c=sqlite3.connect(os.getenv('ELLE_DB','oneai_omni.sqlite3'),timeout=10); c.row_factory=sqlite3.Row
 try:
  c.executescript('''CREATE TABLE IF NOT EXISTS elle_tasks(id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL,owner_id TEXT NOT NULL,objective TEXT NOT NULL,expected_outcome TEXT NOT NULL,constraints_json TEXT NOT NULL,knowledge_refs_json TEXT NOT NULL,capabilities_json TEXT NOT NULL,state TEXT NOT NULL,risk_level TEXT NOT NULL,approval_required INTEGER NOT NULL,approved_by TEXT,approval_at TEXT,execution_result_json TEXT,verification_json TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,completed_at TEXT); CREATE INDEX IF NOT EXISTS idx_elle_workspace ON elle_tasks(workspace_id,updated_at); CREATE TABLE IF NOT EXISTS elle_task_events(id TEXT PRIMARY KEY,task_id TEXT NOT NULL,workspace_id TEXT NOT NULL,event_type TEXT NOT NULL,actor_id TEXT,payload_json TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(task_id) REFERENCES elle_tasks(id));''')
  c.execute('PRAGMA foreign_keys=ON')
  with c: yield c
 finally:c.close()
def _ws(w):
 w=str(w or '').strip()
 if not w: raise ValueError('workspace_id_required')
 return w
def _event(c,tid,w,typ,actor,payload): c.execute('INSERT INTO elle_task_events VALUES(?,?,?,?,?,?,?)',('EVT-'+uuid.uuid4().hex,tid,w,typ,actor,json.dumps(payload,sort_keys=True),now()))
def _item(r):
 if not r:return None
 d=dict(r)
 for k in ('constraints_json','knowledge_refs_json','capabilities_json','execution_result_json','verification_json'):
  v=d.pop(k); d[k[:-5]]=json.loads(v) if v else None
 d['approval_required']=bool(d['approval_required']); return d
def create_task(workspace_id,owner_id,objective,expected_outcome,*,constraints=None,knowledge_refs=None,capabilities=None,risk_level='low',approval_required=False):
 w=_ws(workspace_id)
 if not owner_id or not objective or not expected_outcome: raise ValueError('owner_objective_expected_outcome_required')
 if risk_level not in {'low','medium','high','critical'}: raise ValueError('risk_level_invalid')
 if not isinstance(constraints or {},dict) or not isinstance(knowledge_refs or [],list) or not isinstance(capabilities or [],list): raise ValueError('invalid_task_metadata')
 tid,t=uid(),now()
 with db() as c:
  c.execute('INSERT INTO elle_tasks(id,workspace_id,owner_id,objective,expected_outcome,constraints_json,knowledge_refs_json,capabilities_json,state,risk_level,approval_required,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(tid,w,owner_id,objective,expected_outcome,json.dumps(constraints or {},sort_keys=True),json.dumps(knowledge_refs or []),json.dumps(capabilities or []),'UNDERSTAND',risk_level,int(bool(approval_required or risk_level in {'high','critical'})),t,t))
  _event(c,tid,w,'task.created',owner_id,{'state':'UNDERSTAND'})
 return get_task(tid,w)
def get_task(task_id,workspace_id):
 w=_ws(workspace_id)
 with db() as c:
  r=c.execute('SELECT * FROM elle_tasks WHERE id=? AND workspace_id=?',(task_id,w)).fetchone()
  if not r:return None
  d=_item(r); d['events']=[{**dict(e),'payload':json.loads(e['payload_json'])} for e in c.execute('SELECT * FROM elle_task_events WHERE task_id=? AND workspace_id=? ORDER BY created_at',(task_id,w))]; return d
def transition(task_id,workspace_id,actor_id,new_state,*,detail=None):
 w=_ws(workspace_id); ns=str(new_state or '').upper()
 if ns not in STATES: raise ValueError('task_state_invalid')
 with db() as c:
  r=c.execute('SELECT state,approval_required,approved_by FROM elle_tasks WHERE id=? AND workspace_id=?',(task_id,w)).fetchone()
  if not r:return None
  old=r['state']
  if ns not in NEXT[old]: raise ValueError('invalid_task_transition')
  if ns=='EXECUTE' and r['approval_required'] and not r['approved_by']: raise PermissionError('approval_required')
  t=now(); c.execute('UPDATE elle_tasks SET state=?,updated_at=?,completed_at=? WHERE id=? AND workspace_id=?',(ns,t,t if ns in {'COMPLETED','FAILED'} else None,task_id,w)); _event(c,task_id,w,'task.transition',actor_id,{'from':old,'to':ns,'detail':detail or {}})
 return get_task(task_id,w)
def approve_task(task_id,workspace_id,approver_id,*,authorized):
 w=_ws(workspace_id)
 if not authorized or not approver_id or str(approver_id).startswith('model'): raise PermissionError('authorized_human_approval_required')
 with db() as c:
  r=c.execute('SELECT state FROM elle_tasks WHERE id=? AND workspace_id=?',(task_id,w)).fetchone()
  if not r:return None
  if r['state']!='APPROVE': raise ValueError('task_not_awaiting_approval')
  t=now(); c.execute('UPDATE elle_tasks SET approved_by=?,approval_at=?,updated_at=? WHERE id=? AND workspace_id=?',(approver_id,t,t,task_id,w)); _event(c,task_id,w,'task.approved',approver_id,{'approved':True})
 return get_task(task_id,w)
def submit_verification(task_id,workspace_id,actor_id,result,evidence):
 w=_ws(workspace_id)
 if result not in {'passed','failed','inconclusive'} or not evidence: raise ValueError('verification_result_and_evidence_required')
 with db() as c:
  r=c.execute('SELECT state FROM elle_tasks WHERE id=? AND workspace_id=?',(task_id,w)).fetchone()
  if not r:return None
  if r['state']!='VERIFY': raise ValueError('task_not_in_verify_state')
  p={'result':result,'evidence':evidence,'actor_id':actor_id,'created_at':now()}; c.execute('UPDATE elle_tasks SET verification_json=?,updated_at=? WHERE id=? AND workspace_id=?',(json.dumps(p,sort_keys=True),now(),task_id,w)); _event(c,task_id,w,'task.verified',actor_id,p)
 return get_task(task_id,w)
