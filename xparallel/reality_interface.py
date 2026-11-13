"""Simulation-first, consent-scoped external-world connector boundary."""
from __future__ import annotations
import hashlib,json,sqlite3,threading,uuid
from datetime import datetime,timezone,timedelta
from typing import Any,Callable
_LOCK=threading.RLock()
def _json(v:Any)->str:return json.dumps(v,sort_keys=True,separators=(",",":"),allow_nan=False)
def _sha(v:Any)->str:return hashlib.sha256(_json(v).encode()).hexdigest()

class RealityInterface:
    """Registers scoped connector grants and simulations; physical/external execution is disabled."""
    def __init__(self,*,authenticate:Callable[[Any],dict[str,Any]],
        authorize:Callable[[dict[str,str],str,str],bool],
        verify_consent:Callable[[dict[str,str],str,str],bool],
        simulate:Callable[[str,dict[str,Any]],dict[str,Any]],
        db_path:str=":memory:"):
        if not all(callable(x) for x in (authenticate,authorize,verify_consent,simulate)):
            raise TypeError("trusted_reality_adapters_required")
        self._auth,self._authz,self._consent,self._simulate=authenticate,authorize,verify_consent,simulate
        self._db=sqlite3.connect(db_path,check_same_thread=False);self._db.row_factory=sqlite3.Row
        self._db.executescript("""
        CREATE TABLE IF NOT EXISTS reality_connectors(
          connector_id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL,owner TEXT NOT NULL,
          connector_type TEXT NOT NULL,environment TEXT NOT NULL,scopes_json TEXT NOT NULL,
          expires_at TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reality_events(
          event_id INTEGER PRIMARY KEY AUTOINCREMENT,workspace_id TEXT NOT NULL,
          connector_id TEXT NOT NULL,event TEXT NOT NULL,actor TEXT NOT NULL,
          details_json TEXT NOT NULL,created_at TEXT NOT NULL);
        """);self._db.commit()
    def _principal(self,session:Any)->dict[str,str]:
        p=self._auth(session)
        if not isinstance(p,dict) or p.get("authenticated") is not True:raise PermissionError("authentication_required")
        if any(not isinstance(p.get(k),str) or not p[k].strip() for k in ("workspace_id","subject")):raise PermissionError("invalid_principal")
        return {"workspace_id":p["workspace_id"],"subject":p["subject"]}
    def _allow(self,p:dict[str,str],action:str,target:str)->None:
        if self._authz(p,action,target) is not True:raise PermissionError("reality_action_denied")
    def register(self,session:Any,*,connector_id:str,connector_type:str,scopes:list[str],
        consent_ref:str,expires_in_seconds:int=3600)->dict[str,Any]:
        p=self._principal(session);self._allow(p,"connector","register")
        for value in (connector_id,connector_type,consent_ref):
            if not isinstance(value,str) or not value.strip() or len(value)>120:raise ValueError("invalid_connector_metadata")
        if not isinstance(scopes,list) or not scopes or len(scopes)>20 or any(not isinstance(s,str) or not s.strip() or len(s)>160 or s.strip() in {"*","**"} or "*" in s for s in scopes):
            raise ValueError("explicit_connector_scopes_required")
        if len(set(scopes))!=len(scopes):raise ValueError("duplicate_connector_scope")
        if not isinstance(expires_in_seconds,int) or isinstance(expires_in_seconds,bool) or not 60<=expires_in_seconds<=86400:
            raise ValueError("connector_consent_expiry_out_of_range")
        if self._consent(p,connector_id,consent_ref) is not True:raise PermissionError("verified_operator_consent_required")
        now=datetime.now(timezone.utc);expiry=now+timedelta(seconds=expires_in_seconds)
        with _LOCK,self._db:
            if self._db.execute("SELECT 1 FROM reality_connectors WHERE connector_id=?",(connector_id,)).fetchone():
                raise ValueError("connector_id_already_exists")
            self._db.execute("INSERT INTO reality_connectors VALUES (?,?,?,?,?,?,?,?,?)",
              (connector_id,p["workspace_id"],p["subject"],connector_type,"simulation_only",_json(sorted(scopes)),expiry.isoformat(),"active",now.isoformat()))
            self._event(p,connector_id,"registered",{"connector_type":connector_type,"scopes":sorted(scopes),"environment":"simulation_only"})
        return {"connector_id":connector_id,"status":"active","environment":"simulation_only",
            "scopes":sorted(scopes),"expires_at":expiry.isoformat(),"external_execution_enabled":False}
    def simulate_action(self,session:Any,*,connector_id:str,scope:str,payload:dict[str,Any])->dict[str,Any]:
        p=self._principal(session);self._allow(p,"connector","simulate")
        if not isinstance(payload,dict) or len(_json(payload))>20000:raise ValueError("invalid_simulation_payload")
        with _LOCK:
            row=self._db.execute("SELECT * FROM reality_connectors WHERE connector_id=? AND workspace_id=?",
                (connector_id,p["workspace_id"])).fetchone()
            if not row or row["status"]!="active":raise PermissionError("connector_not_active")
            if datetime.fromisoformat(row["expires_at"])<=datetime.now(timezone.utc):raise PermissionError("connector_consent_expired")
            if scope not in json.loads(row["scopes_json"]):raise PermissionError("connector_scope_not_granted")
            # This boundary intentionally invokes only a simulation adapter.
            result=self._simulate(row["connector_type"],payload)
            if not isinstance(result,dict):raise ValueError("invalid_simulation_result")
            event={"scope":scope,"payload_digest":_sha(payload),"result_digest":_sha(result),"result":result}
            self._event(p,connector_id,"simulated",event)
        return {"connector_id":connector_id,"status":"simulated","scope":scope,
            "result":result,"payload_digest":event["payload_digest"],
            "result_digest":event["result_digest"],"external_execution_performed":False}
    def revoke(self,session:Any,*,connector_id:str,reason:str)->dict[str,Any]:
        p=self._principal(session);self._allow(p,"connector","revoke")
        if not isinstance(reason,str) or not reason.strip():raise ValueError("revocation_reason_required")
        with _LOCK,self._db:
            row=self._db.execute("SELECT status FROM reality_connectors WHERE connector_id=? AND workspace_id=?",
                (connector_id,p["workspace_id"])).fetchone()
            if not row:raise LookupError("connector_not_found")
            if row["status"]=="revoked":return {"connector_id":connector_id,"status":"revoked"}
            self._db.execute("UPDATE reality_connectors SET status='revoked' WHERE connector_id=?",(connector_id,))
            self._event(p,connector_id,"revoked",{"reason":reason[:500],"emergency_revocation":True})
        return {"connector_id":connector_id,"status":"revoked","future_simulation_blocked":True}
    def _event(self,p:dict[str,str],connector_id:str,event:str,details:dict[str,Any])->None:
        self._db.execute("INSERT INTO reality_events(workspace_id,connector_id,event,actor,details_json,created_at) VALUES (?,?,?,?,?,?)",
          (p["workspace_id"],connector_id,event,p["subject"],_json(details),datetime.now(timezone.utc).isoformat()))
    def audit(self,session:Any,*,connector_id:str)->list[dict[str,Any]]:
        p=self._principal(session);self._allow(p,"connector","audit")
        rows=self._db.execute("SELECT event,actor,details_json,created_at FROM reality_events WHERE workspace_id=? AND connector_id=? ORDER BY event_id",
          (p["workspace_id"],connector_id)).fetchall()
        return [{"event":r["event"],"actor":r["actor"],"details":json.loads(r["details_json"]),"created_at":r["created_at"]} for r in rows]
    def close(self)->None:self._db.close()
