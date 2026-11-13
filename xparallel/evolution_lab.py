"""Reproducible, approval-gated evaluation and versioned evolution proposals."""
from __future__ import annotations
import hashlib,json,sqlite3,threading,uuid
from datetime import datetime,timezone
from typing import Any,Callable

_LOCK=threading.RLock()
def _canon(value:Any)->bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()
def _digest(value:Any)->str:return hashlib.sha256(_canon(value)).hexdigest()

class EvolutionLab:
    """Records experiments and human-approved staged proposals; never modifies live systems."""
    def __init__(self,*,authenticate:Callable[[Any],dict[str,Any]],
        authorize:Callable[[dict[str,str],str,str],bool],
        verify_approval:Callable[[dict[str,str],str,str],bool],
        run_evaluation:Callable[[dict[str,Any],dict[str,Any]],dict[str,Any]],
        db_path:str=":memory:"):
        if not all(callable(x) for x in (authenticate,authorize,verify_approval,run_evaluation)):
            raise TypeError("trusted_evolution_adapters_required")
        self._auth,self._authz,self._approval,self._runner=authenticate,authorize,verify_approval,run_evaluation
        self._db=sqlite3.connect(db_path,check_same_thread=False); self._db.row_factory=sqlite3.Row
        self._db.executescript("""
        CREATE TABLE IF NOT EXISTS evolution_experiments(
          experiment_id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL,owner TEXT NOT NULL,
          baseline_version TEXT NOT NULL,candidate_version TEXT NOT NULL,dataset_digest TEXT NOT NULL,
          config_digest TEXT NOT NULL,status TEXT NOT NULL,results_json TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS evolution_proposals(
          proposal_id TEXT PRIMARY KEY,workspace_id TEXT NOT NULL,experiment_id TEXT NOT NULL,
          baseline_version TEXT NOT NULL,candidate_version TEXT NOT NULL,artifact_digest TEXT NOT NULL,
          status TEXT NOT NULL,approval_ref TEXT,created_at TEXT NOT NULL,
          FOREIGN KEY(experiment_id) REFERENCES evolution_experiments(experiment_id));
        CREATE TABLE IF NOT EXISTS evolution_events(
          event_id INTEGER PRIMARY KEY AUTOINCREMENT,workspace_id TEXT NOT NULL,
          proposal_id TEXT NOT NULL,event TEXT NOT NULL,actor TEXT NOT NULL,details_json TEXT NOT NULL,
          created_at TEXT NOT NULL);
        """); self._db.commit()
    def _principal(self,session:Any)->dict[str,str]:
        p=self._auth(session)
        if not isinstance(p,dict) or p.get("authenticated") is not True:raise PermissionError("authentication_required")
        if not all(isinstance(p.get(k),str) and p[k].strip() for k in ("workspace_id","subject")):raise PermissionError("invalid_principal")
        return {"workspace_id":p["workspace_id"],"subject":p["subject"]}
    def _allow(self,p:dict[str,str],action:str,target:str)->None:
        if self._authz(p,action,target) is not True:raise PermissionError("evolution_action_denied")
    def run_experiment(self,session:Any,*,baseline_version:str,candidate_version:str,
        dataset:list[dict[str,Any]],config:dict[str,Any])->dict[str,Any]:
        p=self._principal(session);self._allow(p,"experiment","create")
        if not all(isinstance(x,str) and x.strip() and len(x)<=120 for x in (baseline_version,candidate_version)) or baseline_version==candidate_version:
            raise ValueError("invalid_version_pair")
        if not isinstance(dataset,list) or not dataset or len(dataset)>10000 or not isinstance(config,dict):
            raise ValueError("invalid_experiment_dataset_or_config")
        ds=[x for x in dataset]
        dataset_digest=_digest(ds);config_digest=_digest(config)
        experiment_id=uuid.uuid4().hex
        result=self._runner({"baseline_version":baseline_version,"candidate_version":candidate_version,
            "dataset":ds,"dataset_digest":dataset_digest,"config":config,"config_digest":config_digest},
            {"workspace_id":p["workspace_id"],"actor":p["subject"],"experiment_id":experiment_id})
        if not isinstance(result,dict) or not isinstance(result.get("metrics"),dict):
            raise ValueError("evaluation_runner_must_return_metrics")
        metrics=result["metrics"]
        for key,value in metrics.items():
            if not isinstance(key,str) or not isinstance(value,(int,float)) or isinstance(value,bool):
                raise ValueError("metrics_must_be_numeric")
        now=datetime.now(timezone.utc).isoformat()
        record={"metrics":metrics,"baseline_metrics":result.get("baseline_metrics",{}),
            "candidate_metrics":result.get("candidate_metrics",{}),"regressions":result.get("regressions",[]),
            "runner_id":str(result.get("runner_id","injected-runner"))[:120]}
        with _LOCK,self._db:
            self._db.execute("INSERT INTO evolution_experiments VALUES (?,?,?,?,?,?,?,?,?,?)",
              (experiment_id,p["workspace_id"],p["subject"],baseline_version,candidate_version,
               dataset_digest,config_digest,"evaluated",_canon(record).decode(),now))
        return {"experiment_id":experiment_id,"status":"evaluated","dataset_digest":dataset_digest,
            "config_digest":config_digest,**record}
    def propose(self,session:Any,*,experiment_id:str,artifact_digest:str)->dict[str,Any]:
        p=self._principal(session);self._allow(p,"proposal","create")
        if not isinstance(artifact_digest,str) or len(artifact_digest)!=64 or any(c not in "0123456789abcdef" for c in artifact_digest):
            raise ValueError("artifact_digest_must_be_sha256")
        with _LOCK,self._db:
            exp=self._db.execute("SELECT * FROM evolution_experiments WHERE experiment_id=? AND workspace_id=?",
                (experiment_id,p["workspace_id"])).fetchone()
            if not exp:raise LookupError("experiment_not_found")
            result=json.loads(exp["results_json"])
            if result.get("regressions"):raise ValueError("regressions_block_proposal")
            proposal_id=uuid.uuid4().hex;now=datetime.now(timezone.utc).isoformat()
            self._db.execute("INSERT INTO evolution_proposals VALUES (?,?,?,?,?,?,?,?,?)",
              (proposal_id,p["workspace_id"],experiment_id,exp["baseline_version"],exp["candidate_version"],
               artifact_digest,"proposed",None,now))
            self._event(p,proposal_id,"proposed",{"artifact_digest":artifact_digest})
        return {"proposal_id":proposal_id,"status":"proposed","requires_human_approval":True,
            "live_change_performed":False}
    def stage(self,session:Any,*,proposal_id:str,approval_ref:str)->dict[str,Any]:
        p=self._principal(session);self._allow(p,"proposal","stage")
        if not isinstance(approval_ref,str) or not approval_ref.strip() or len(approval_ref)>200:raise ValueError("approval_reference_required")
        with _LOCK,self._db:
            row=self._db.execute("SELECT * FROM evolution_proposals WHERE proposal_id=? AND workspace_id=?",
                (proposal_id,p["workspace_id"])).fetchone()
            if not row or row["status"]!="proposed":raise ValueError("proposal_not_stageable")
            if self._approval(p,proposal_id,approval_ref) is not True:raise PermissionError("independent_human_approval_required")
            self._db.execute("UPDATE evolution_proposals SET status='staged',approval_ref=? WHERE proposal_id=?",
                (approval_ref,proposal_id))
            self._event(p,proposal_id,"staged",{"approval_ref":approval_ref})
        return {"proposal_id":proposal_id,"status":"staged","live_change_performed":False}
    def promote(self,session:Any,*,proposal_id:str,approval_ref:str)->dict[str,Any]:
        p=self._principal(session);self._allow(p,"proposal","promote")
        with _LOCK,self._db:
            row=self._db.execute("SELECT * FROM evolution_proposals WHERE proposal_id=? AND workspace_id=?",
                (proposal_id,p["workspace_id"])).fetchone()
            if not row or row["status"]!="staged":raise ValueError("proposal_not_promotable")
            if self._approval(p,proposal_id,approval_ref) is not True:raise PermissionError("separate_promotion_approval_required")
            self._db.execute("UPDATE evolution_proposals SET status='promoted' WHERE proposal_id=?",(proposal_id,))
            self._event(p,proposal_id,"promoted",{"approval_ref":approval_ref,"meaning":"record_only_no_deployment"})
        return {"proposal_id":proposal_id,"status":"promoted","deployment_performed":False}
    def rollback(self,session:Any,*,proposal_id:str,reason:str)->dict[str,Any]:
        p=self._principal(session);self._allow(p,"proposal","rollback")
        if not isinstance(reason,str) or not reason.strip():raise ValueError("rollback_reason_required")
        with _LOCK,self._db:
            row=self._db.execute("SELECT * FROM evolution_proposals WHERE proposal_id=? AND workspace_id=?",
                (proposal_id,p["workspace_id"])).fetchone()
            if not row or row["status"] not in {"staged","promoted"}:raise ValueError("proposal_not_rollbackable")
            self._db.execute("UPDATE evolution_proposals SET status='rolled_back' WHERE proposal_id=?",(proposal_id,))
            self._event(p,proposal_id,"rolled_back",{"reason":reason[:500],"meaning":"record_only_no_live_rollback"})
        return {"proposal_id":proposal_id,"status":"rolled_back","live_rollback_performed":False}
    def _event(self,p:dict[str,str],proposal_id:str,event:str,details:dict[str,Any])->None:
        self._db.execute("INSERT INTO evolution_events(workspace_id,proposal_id,event,actor,details_json,created_at) VALUES (?,?,?,?,?,?)",
          (p["workspace_id"],proposal_id,event,p["subject"],_canon(details).decode(),datetime.now(timezone.utc).isoformat()))
    def history(self,session:Any,*,proposal_id:str)->list[dict[str,Any]]:
        p=self._principal(session);self._allow(p,"proposal","read")
        rows=self._db.execute("SELECT event,actor,details_json,created_at FROM evolution_events WHERE workspace_id=? AND proposal_id=? ORDER BY event_id",
          (p["workspace_id"],proposal_id)).fetchall()
        return [{"event":r["event"],"actor":r["actor"],"details":json.loads(r["details_json"]),"created_at":r["created_at"]} for r in rows]
    def close(self)->None:self._db.close()
