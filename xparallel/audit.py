"""Durable audit event model for security-sensitive XParallel actions."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib, json
from typing import Any
SENSITIVE_ACTIONS={"solution_created","graph_search","verification","deployment_requested","deployment_approved","deployment_rejected","billing_preview","repair_job_planned","arot:elle.task.created","arot:elle.task.transition","arot:elle.task.approved","arot:elle.task.verified","arot:omni.record.created","arot:omni.search","arot:omni.record.verification","arot:parallel.research.completed","arot:xparallel.task.dispatched"}
def audit_event(action:str, workspace_id:str, actor:str="system", metadata:dict[str,Any]|None=None)->dict[str,Any]:
    if action not in SENSITIVE_ACTIONS: raise ValueError("unknown_audit_action")
    event={"action":action,"workspace_id":workspace_id,"actor":actor,"created_at":datetime.now(timezone.utc).isoformat(),"metadata":metadata or {}}
    event["event_fingerprint"]=hashlib.sha256(json.dumps(event,sort_keys=True).encode()).hexdigest()
    return event
