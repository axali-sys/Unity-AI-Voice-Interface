"""Bounded, attributable specialist collaboration with independent verification."""
from __future__ import annotations
import hashlib
from typing import Any, Callable

class ParallelIntelligence:
    """Coordinate bounded specialist proposals; never execute external actions."""
    def __init__(self,*,specialists:dict[str,Callable[[dict[str,Any]],dict[str,Any]]],
        verify_contribution:Callable[[str,str,dict[str,Any]],dict[str,Any]],
        synthesize:Callable[[str,list[dict[str,Any]]],dict[str,Any]],
        max_agents:int=3,max_task_chars:int=10000,max_context_chars:int=20000,
        max_output_chars:int=30000,max_specialist_output_chars:int=8000):
        if not isinstance(specialists,dict) or not specialists or any(not isinstance(k,str) or not callable(v) for k,v in specialists.items()):
            raise TypeError("specialist_adapters_required")
        if not callable(verify_contribution) or not callable(synthesize): raise TypeError("verification_and_synthesis_adapters_required")
        if not 1<=max_agents<=5 or not 100<=max_task_chars<=50000 or not 0<=max_context_chars<=100000:
            raise ValueError("collaboration_limits_out_of_range")
        if not 100<=max_output_chars<=200000 or not 100<=max_specialist_output_chars<=50000:
            raise ValueError("collaboration_output_limits_out_of_range")
        if verify_contribution in specialists.values(): raise ValueError("independent_verifier_required")
        self._specialists=dict(specialists); self._verify=verify_contribution; self._synthesize=synthesize
        self._max_agents=max_agents; self._max_task=max_task_chars; self._max_context=max_context_chars
        self._max_output=max_output_chars; self._max_each=max_specialist_output_chars

    def collaborate(self,task:str,*,context:str="",roles:list[str]|None=None)->dict[str,Any]:
        if not isinstance(task,str) or not task.strip() or len(task)>self._max_task: raise ValueError("invalid_collaboration_task")
        if not isinstance(context,str) or len(context)>self._max_context: raise ValueError("collaboration_context_too_large")
        selected=roles if roles is not None else list(self._specialists)
        if not isinstance(selected,list) or not selected or len(selected)>self._max_agents:
            raise ValueError("collaboration_agent_budget_exceeded")
        if len(set(selected))!=len(selected) or any(role not in self._specialists for role in selected):
            raise ValueError("unknown_or_duplicate_specialist")
        contributions=[]; verified=[]; output_chars=0
        for role in selected:
            specialist=self._specialists[role]
            try:
                raw=specialist({"task":task,"context":context,"max_output_chars":self._max_each})
                if not isinstance(raw,dict) or not isinstance(raw.get("content"),str) or not raw["content"].strip():
                    raise ValueError("invalid_specialist_response")
                content=raw["content"].strip()
                if len(content)>self._max_each: raise ValueError("specialist_output_budget_exceeded")
                refs=raw.get("evidence_refs",[])
                if not isinstance(refs,list) or len(refs)>50 or any(not isinstance(x,str) or not x.strip() or len(x)>500 for x in refs):
                    raise ValueError("invalid_evidence_references")
                output_chars+=len(content)
                if output_chars>self._max_output: raise ValueError("collaboration_total_output_budget_exceeded")
                item={"specialist":role,"content":content,"evidence_refs":refs,
                      "content_sha256":hashlib.sha256(content.encode()).hexdigest()}
                try:
                    review=self._verify(task,role,item)
                    status=review.get("status") if isinstance(review,dict) else None
                    if status not in {"verified","inconclusive","rejected"}: status="inconclusive"
                    item["verification"]={"status":status,"reviewer":str(review.get("reviewer","independent-reviewer"))[:120],
                        "evidence_refs":review.get("evidence_refs",[]) if isinstance(review.get("evidence_refs",[]),list) else []}
                except Exception as exc:
                    item["verification"]={"status":"inconclusive","error":type(exc).__name__}
                contributions.append(item)
                if item["verification"]["status"]=="verified": verified.append(item)
            except Exception as exc:
                contributions.append({"specialist":role,"verification":{"status":"inconclusive","error":type(exc).__name__}})
        if not verified:
            return {"status":"insufficient_verified_evidence","contributions":contributions,
                    "synthesis":None,"human_review_required":True,"execution_performed":False}
        try:
            result=self._synthesize(task,verified)
        except Exception as exc:
            return {"status":"synthesis_failed","contributions":contributions,"synthesis":None,
                    "synthesis_error":type(exc).__name__,"human_review_required":True,"execution_performed":False}
        if not isinstance(result,dict) or not isinstance(result.get("content"),str) or not result["content"].strip():
            raise ValueError("invalid_synthesis_response")
        synthesis=result["content"].strip()
        if len(synthesis)>self._max_output: raise ValueError("synthesis_output_budget_exceeded")
        conflicts=result.get("conflicts",[])
        if not isinstance(conflicts,list) or len(conflicts)>50: raise ValueError("invalid_conflict_list")
        unresolved=bool(conflicts) or len(verified)!=len(contributions)
        return {"status":"disagreement_requires_review" if unresolved else "synthesized",
            "contributions":contributions,"verified_specialists":[x["specialist"] for x in verified],
            "synthesis":synthesis,"conflicts":conflicts,
            "human_review_required":True,"execution_performed":False,
            "budget":{"agents_used":len(selected),"output_chars":output_chars+len(synthesis)}}
