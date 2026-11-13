"""Authenticated host boundary for Parallel Verse workspace operations."""
from __future__ import annotations
from typing import Any,Callable
from xparallel import parallel_verse as store

class ParallelVerseService:
    """Derive workspace from trusted session; never accept workspace from request data."""
    def __init__(self,*,authenticate:Callable[[Any],dict[str,Any]],
        authorize:Callable[[dict[str,str],str,str],bool],db_path:str|None=None):
        if not callable(authenticate) or not callable(authorize): raise TypeError("trusted_verse_auth_and_acl_required")
        self._authenticate,self._authorize,self._db=authenticate,authorize,db_path

    def _principal(self,session:Any)->dict[str,str]:
        raw=self._authenticate(session)
        if not isinstance(raw,dict) or raw.get("authenticated") is not True: raise PermissionError("caller_not_authenticated")
        workspace,subject=raw.get("workspace_id"),raw.get("subject")
        if not isinstance(workspace,str) or not workspace.strip() or len(workspace)>200: raise PermissionError("trusted_workspace_missing")
        if not isinstance(subject,str) or not subject.strip() or len(subject)>200: raise PermissionError("trusted_subject_missing")
        return {"workspace_id":workspace.strip(),"subject":subject.strip()}

    def _allow(self,principal:dict[str,str],action:str,resource:str="workspace")->None:
        if self._authorize(principal,action,resource) is not True: raise PermissionError("parallel_verse_access_denied")

    @staticmethod
    def _metadata(value:Any)->dict[str,Any]:
        if value is None:return {}
        if not isinstance(value,dict): raise ValueError("metadata_must_be_object")
        forbidden=("password","secret","token","private_key","api_key","credential")
        def scan(item:Any)->None:
            if isinstance(item,dict):
                for key,child in item.items():
                    if any(word in str(key).lower().replace("-","_") for word in forbidden):
                        raise ValueError("secret_field_not_allowed")
                    scan(child)
            elif isinstance(item,list):
                for child in item: scan(child)
        scan(value)
        return value

    def register_agent(self,session:Any,*,name:str,kind:str="general",metadata:dict[str,Any]|None=None)->dict[str,Any]:
        p=self._principal(session); self._allow(p,"agent.create")
        return store.register_agent(p["workspace_id"],name,kind,self._metadata(metadata),db_path=self._db)

    def list_agents(self,session:Any,limit:int=50)->list[dict[str,Any]]:
        p=self._principal(session); self._allow(p,"agent.read")
        return store.list_agents(p["workspace_id"],limit,self._db)

    def create_space(self,session:Any,*,name:str,description:str="")->dict[str,Any]:
        p=self._principal(session); self._allow(p,"space.create")
        return store.create_space(p["workspace_id"],name,description,self._db)

    def list_spaces(self,session:Any,limit:int=50)->list[dict[str,Any]]:
        p=self._principal(session); self._allow(p,"space.read")
        return store.list_spaces(p["workspace_id"],limit,self._db)

    def record_event(self,session:Any,*,event_type:str,payload:dict[str,Any]|None=None,
        space_id:str|None=None,agent_id:str|None=None)->dict[str,Any]:
        p=self._principal(session); self._allow(p,"event.write",space_id or agent_id or "workspace")
        return store.record_event(p["workspace_id"],event_type,payload,space_id,agent_id,self._db)

    def list_events(self,session:Any,limit:int=50)->list[dict[str,Any]]:
        p=self._principal(session); self._allow(p,"event.read")
        return store.list_events(p["workspace_id"],limit,self._db)

    def create_task(self,session:Any,*,title:str,description:str="",space_id:str|None=None,
        created_by:str|None=None,assigned_to:str|None=None)->dict[str,Any]:
        p=self._principal(session); self._allow(p,"task.create",space_id or "workspace")
        return store.create_task(p["workspace_id"],title,description,space_id,created_by,assigned_to,self._db)

    def list_tasks(self,session:Any,limit:int=50)->list[dict[str,Any]]:
        p=self._principal(session); self._allow(p,"task.read")
        return store.list_tasks(p["workspace_id"],limit,self._db)
