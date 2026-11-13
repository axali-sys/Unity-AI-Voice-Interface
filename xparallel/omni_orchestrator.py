"""Fail-closed typed Omni workflow planning and gated execution."""
from __future__ import annotations
import re
from typing import Any,Callable

_ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,99}$")

class OmniOrchestrator:
    """Topologically plan workflows; execute only through injected trusted gates."""
    def __init__(self,*,authorize_step:Callable[[Any,dict[str,Any]],dict[str,Any]],
        check_approval:Callable[[Any,dict[str,Any]],dict[str,Any]],
        execute_step:Callable[[Any,dict[str,Any]],dict[str,Any]],
        record_receipt:Callable[[Any,dict[str,Any],dict[str,Any]],Any],
        retry_wait:Callable[[int],Any],max_steps:int=50,max_attempts:int=3):
        callbacks=(authorize_step,check_approval,execute_step,record_receipt,retry_wait)
        if not all(callable(x) for x in callbacks): raise TypeError("trusted_omni_adapters_required")
        if not 1<=max_steps<=200 or not 1<=max_attempts<=5: raise ValueError("omni_limits_out_of_range")
        self._authorize,self._approval,self._execute,self._receipt,self._wait=callbacks
        self._max_steps,self._max_attempts=max_steps,max_attempts

    def plan(self,workflow:dict[str,Any])->dict[str,Any]:
        if not isinstance(workflow,dict) or not isinstance(workflow.get("steps"),list): raise ValueError("workflow_steps_required")
        steps=workflow["steps"]
        if not steps or len(steps)>self._max_steps: raise ValueError("workflow_step_budget_exceeded")
        indexed={}
        for step in steps:
            if not isinstance(step,dict): raise ValueError("invalid_workflow_step")
            sid=step.get("step_id")
            if not isinstance(sid,str) or not _ID.fullmatch(sid) or sid in indexed: raise ValueError("invalid_or_duplicate_step_id")
            if not isinstance(step.get("action"),str) or not _ID.fullmatch(step["action"]): raise ValueError("invalid_workflow_action")
            if not isinstance(step.get("resource_scope"),str) or not step["resource_scope"].strip() or len(step["resource_scope"])>500:
                raise ValueError("invalid_workflow_resource_scope")
            if not isinstance(step.get("input",{}),dict): raise ValueError("workflow_input_must_be_object")
            deps=step.get("depends_on",[])
            if not isinstance(deps,list) or any(not isinstance(x,str) for x in deps) or len(set(deps))!=len(deps):
                raise ValueError("invalid_workflow_dependencies")
            consequential=step.get("consequential",False)
            requires=step.get("requires_approval",False)
            idempotent=step.get("idempotent",False)
            if any(not isinstance(x,bool) for x in (consequential,requires,idempotent)): raise ValueError("invalid_workflow_flags")
            if consequential and not requires: raise ValueError("consequential_step_requires_human_approval")
            indexed[sid]={**step,"depends_on":deps}
        for sid,step in indexed.items():
            if sid in step["depends_on"] or any(dep not in indexed for dep in step["depends_on"]):
                raise ValueError("unknown_or_self_workflow_dependency")
        ordered=[]; pending=set(indexed); completed=set()
        while pending:
            ready=sorted(sid for sid in pending if set(indexed[sid]["depends_on"])<=completed)
            if not ready: raise ValueError("workflow_dependency_cycle")
            for sid in ready: ordered.append(indexed[sid]); pending.remove(sid); completed.add(sid)
        return {"workflow_id":str(workflow.get("workflow_id","workflow"))[:100],
            "steps":[{"step_id":s["step_id"],"action":s["action"],"resource_scope":s["resource_scope"],
                "depends_on":s["depends_on"],"consequential":s.get("consequential",False),
                "requires_approval":s.get("requires_approval",False),"idempotent":s.get("idempotent",False)} for s in ordered],
            "execution_performed":False}

    def execute(self,session:Any,workflow:dict[str,Any])->dict[str,Any]:
        plan=self.plan(workflow); source={s["step_id"]:s for s in workflow["steps"]}
        statuses={}; events=[]; attempts_total=0
        for planned in plan["steps"]:
            step=source[planned["step_id"]]
            blocked=[dep for dep in planned["depends_on"] if statuses.get(dep)!="completed"]
            if blocked:
                statuses[planned["step_id"]]="skipped_dependency"
                events.append({"step_id":planned["step_id"],"status":"skipped_dependency","blocked_by":blocked})
                continue
            max_attempts=self._max_attempts if planned["idempotent"] else 1
            step_result=None; final_status="failed"
            for attempt in range(1,max_attempts+1):
                attempts_total+=1
                if attempts_total>self._max_steps*self._max_attempts: raise RuntimeError("workflow_attempt_budget_exceeded")
                try: decision=self._authorize(session,step)
                except Exception: decision={"allowed":False,"reason":"authorization_adapter_failed"}
                if not isinstance(decision,dict) or decision.get("allowed") is not True:
                    final_status="blocked_policy"; step_result={"reason":str(decision.get("reason","authorization_denied")) if isinstance(decision,dict) else "authorization_denied"}; break
                approval_ticket=None
                if planned["requires_approval"]:
                    try: approval=self._approval(session,step)
                    except Exception: approval={"approved":False}
                    if not isinstance(approval,dict) or approval.get("approved") is not True or not isinstance(approval.get("ticket_id"),str) or not approval["ticket_id"].strip():
                        final_status="pending_approval"; step_result={"reason":"valid_human_approval_ticket_required"}; break
                    approval_ticket=approval["ticket_id"]
                try:
                    step_result=self._execute(session,{**step,"approval_ticket_id":approval_ticket})
                    if not isinstance(step_result,dict): raise ValueError("executor_invalid_result")
                    if step_result.get("status")=="completed":
                        receipt=self._receipt(session,step,step_result)
                        if not isinstance(receipt,(str,dict)) or not receipt:
                            final_status="executed_unreceipted"; step_result={"reason":"receipt_not_recorded"}; break
                        final_status="completed"; step_result={**step_result,"receipt":receipt}; break
                    retryable=step_result.get("retryable") is True
                    if not (planned["idempotent"] and retryable and attempt<max_attempts):
                        final_status="failed"; break
                except Exception as exc:
                    step_result={"error":type(exc).__name__}
                    if not (planned["idempotent"] and attempt<max_attempts):
                        final_status="failed"; break
                self._wait(min(2**attempt,30))
            statuses[planned["step_id"]]=final_status
            events.append({"step_id":planned["step_id"],"status":final_status,"result":step_result})
            if final_status not in {"completed"}:
                for later in plan["steps"]:
                    if later["step_id"] not in statuses:
                        statuses[later["step_id"]]="not_started"
                break
        return {"workflow_id":plan["workflow_id"],"status":"completed" if statuses and all(v=="completed" for v in statuses.values()) else "stopped",
            "step_statuses":statuses,"events":events,"attempts":attempts_total,
            "execution_performed":any(e["status"]=="completed" for e in events),
            "human_approval_enforced":True}
