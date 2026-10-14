"""Least-privilege, stdlib-only adapters for Axaliai/XParallel plugins."""
from __future__ import annotations
import json, os, re, urllib.parse, urllib.request, urllib.error
from pathlib import Path
from typing import Any

PLUGIN_REGISTRY = [
 {"id":"web_search","name":"Web search","kind":"tool","purpose":"Search public web results","credential_env":"XP_WEB_SEARCH_API_KEY","adapter":"web_search","permissions":["search_public_web"],"approval_required":False},
 {"id":"github","name":"GitHub","kind":"connected_app","purpose":"Read authorized repositories and issues","credential_env":"GITHUB_TOKEN","adapter":"github","permissions":["repository_read"],"approval_required":False},
 {"id":"google_drive","name":"Google Drive","kind":"connected_app","purpose":"Search and retrieve files authorized by the access token","credential_env":"GOOGLE_DRIVE_ACCESS_TOKEN","adapter":"google_drive","permissions":["drive_file_read"],"approval_required":False},
 {"id":"file_retrieval","name":"File retrieval","kind":"tool","purpose":"Read files inside the configured allowlisted directory","credential_env":"","adapter":"file_retrieval","permissions":["read_authorized_files"],"approval_required":False},
 {"id":"ai_memory","name":"AI Memory","kind":"tool","purpose":"Retrieve relevant saved memory records","credential_env":"","adapter":"ai_memory","permissions":["read_authorized_memory"],"approval_required":False},
 {"id":"xparallel_sandbox","name":"XParallel isolated sandbox","kind":"tool","purpose":"Run supplied tests in isolated Docker without network","credential_env":"","adapter":"xparallel_sandbox","permissions":["sandbox_test"],"approval_required":True},
]
MAX_RESPONSE_BYTES = 1_000_000
MAX_TEXT_CHARS = 12000

def _http_json(url: str, headers: dict[str,str] | None = None, timeout: float = 8) -> Any:
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"Axaliai-PluginAdapter/1.0",**(headers or {})})
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read(MAX_RESPONSE_BYTES+1)
    if len(raw)>MAX_RESPONSE_BYTES: raise ValueError("plugin_response_too_large")
    data=json.loads(raw.decode("utf-8"))
    if not isinstance(data,(dict,list)): raise ValueError("invalid_plugin_response")
    return data

def _text(value: Any, limit: int = MAX_TEXT_CHARS) -> str:
    if isinstance(value,str): return value[:limit]
    return json.dumps(value,ensure_ascii=False,sort_keys=True)[:limit]

def _github(action: str, p: dict) -> dict:
    token=os.getenv("GITHUB_TOKEN","").strip()
    if not token: raise ValueError("credentials_missing:GITHUB_TOKEN")
    headers={"Authorization":f"Bearer {token}","X-GitHub-Api-Version":"2022-11-28"}
    if action=="list_repositories":
        url="https://api.github.com/user/repos?sort=updated&per_page=20"
    elif action=="search_repositories":
        q=str(p.get("query","")).strip()
        if not q: raise ValueError("query_required")
        url="https://api.github.com/search/repositories?q="+urllib.parse.quote(q)+"&per_page=10"
    elif action=="list_issues":
        repo=str(p.get("repo",""))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo): raise ValueError("repo_must_be_owner_slash_name")
        url=f"https://api.github.com/repos/{repo}/issues?state=open&per_page=20"
    elif action=="get_repository":
        repo=str(p.get("repo",""))
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+",repo): raise ValueError("repo_must_be_owner_slash_name")
        url=f"https://api.github.com/repos/{repo}"
    else: raise ValueError("unsupported_github_action")
    data=_http_json(url,headers)
    if action=="list_repositories": data={"items":[{"full_name":x.get("full_name"),"private":x.get("private"),"html_url":x.get("html_url"),"description":x.get("description")} for x in data if isinstance(x,dict)]}
    elif action=="list_issues": data={"items":[{"title":x.get("title"),"state":x.get("state"),"html_url":x.get("html_url"),"number":x.get("number")} for x in data if isinstance(x,dict)]}
    return {"state":"ok","plugin_id":"github","action":action,"data":data}

def _drive(action: str, p: dict) -> dict:
    token=os.getenv("GOOGLE_DRIVE_ACCESS_TOKEN","").strip()
    if not token: raise ValueError("credentials_missing:GOOGLE_DRIVE_ACCESS_TOKEN")
    headers={"Authorization":f"Bearer {token}"}
    if action=="search_files":
        q=str(p.get("query","")).strip()
        if not q: raise ValueError("query_required")
        query=f"name contains '{q.replace(chr(39), chr(92)+chr(39))}' and trashed = false"
        url="https://www.googleapis.com/drive/v3/files?"+urllib.parse.urlencode({"q":query,"pageSize":20,"fields":"files(id,name,mimeType,modifiedTime,webViewLink)"})
        data=_http_json(url,headers)
        return {"state":"ok","plugin_id":"google_drive","action":action,"data":data}
    if action=="get_file":
        file_id=str(p.get("file_id","")).strip()
        if not re.fullmatch(r"[A-Za-z0-9_-]{5,200}",file_id): raise ValueError("valid_file_id_required")
        meta=_http_json("https://www.googleapis.com/drive/v3/files/"+urllib.parse.quote(file_id,safe="")+"?fields=id,name,mimeType,webViewLink",headers)
        mime=meta.get("mimeType","")
        if mime.startswith("application/vnd.google-apps."):
            url="https://www.googleapis.com/drive/v3/files/"+urllib.parse.quote(file_id,safe="")+"/export?mimeType=text/plain"
        else:
            url="https://www.googleapis.com/drive/v3/files/"+urllib.parse.quote(file_id,safe="")+"?alt=media"
        req=urllib.request.Request(url,headers={"Authorization":f"Bearer {token}","User-Agent":"Axaliai-PluginAdapter/1.0"})
        with urllib.request.urlopen(req,timeout=8) as r: raw=r.read(MAX_RESPONSE_BYTES+1)
        if len(raw)>MAX_RESPONSE_BYTES: raise ValueError("plugin_response_too_large")
        return {"state":"ok","plugin_id":"google_drive","action":action,"file":meta,"text":raw.decode("utf-8",errors="replace")[:MAX_TEXT_CHARS]}
    raise ValueError("unsupported_google_drive_action")

def _web_search(action: str, p: dict) -> dict:
    if action!="search": raise ValueError("unsupported_web_search_action")
    key=os.getenv("XP_WEB_SEARCH_API_KEY","").strip()
    if not key: raise ValueError("credentials_missing:XP_WEB_SEARCH_API_KEY")
    q=str(p.get("query","")).strip()
    if not q: raise ValueError("query_required")
    url="https://api.search.brave.com/res/v1/web/search?"+urllib.parse.urlencode({"q":q,"count":min(10,max(1,int(p.get("count",5))))})
    data=_http_json(url,{"X-Subscription-Token":key,"Accept":"application/json"})
    results=[{"title":x.get("title"),"url":x.get("url"),"description":x.get("description")} for x in data.get("web",{}).get("results",[]) if isinstance(x,dict)]
    return {"state":"ok","plugin_id":"web_search","action":action,"results":results}

def _safe_local_path(root: Path, requested: str) -> Path:
    if not requested or "\x00" in requested: raise ValueError("path_required")
    base=root.resolve()
    candidate=(base/requested).resolve()
    if candidate!=base and base not in candidate.parents: raise ValueError("path_outside_allowed_root")
    if not candidate.is_file(): raise ValueError("file_not_found")
    return candidate

def _file_retrieval(action: str, p: dict) -> dict:
    root_text=os.getenv("XP_FILE_RETRIEVAL_ROOT","").strip()
    if not root_text: raise ValueError("configuration_missing:XP_FILE_RETRIEVAL_ROOT")
    root=Path(root_text).resolve()
    if action=="list_files":
        q=str(p.get("query","")).lower()
        items=[]
        for path in root.rglob("*"):
            try:
                if path.is_file() and not path.is_symlink() and (not q or q in path.name.lower()):
                    items.append({"path":str(path.relative_to(root)),"size":path.stat().st_size})
            except OSError: continue
            if len(items)>=50: break
        return {"state":"ok","plugin_id":"file_retrieval","files":items}
    if action=="read_file":
        path=_safe_local_path(root,str(p.get("path","")))
        if path.is_symlink(): raise ValueError("symlinks_not_allowed")
        if path.stat().st_size>MAX_RESPONSE_BYTES: raise ValueError("file_too_large")
        return {"state":"ok","plugin_id":"file_retrieval","path":str(path.relative_to(root)),"text":path.read_text(encoding="utf-8",errors="replace")[:MAX_TEXT_CHARS]}
    raise ValueError("unsupported_file_retrieval_action")

def _memory(action: str, p: dict) -> dict:
    if action!="search": raise ValueError("unsupported_ai_memory_action")
    path_text=os.getenv("XP_AI_MEMORY_PATH","").strip()
    if not path_text: raise ValueError("configuration_missing:XP_AI_MEMORY_PATH")
    path=Path(path_text).resolve()
    if not path.is_file(): raise ValueError("memory_file_not_found")
    query=str(p.get("query","")).strip().lower()
    workspace_id=str(p.get("workspace_id","")).strip()
    if not workspace_id: raise ValueError("workspace_id_required_for_memory_isolation")
    if not query: raise ValueError("query_required")
    terms={x for x in re.findall(r"[a-z0-9]{3,}",query)}
    hits=[]
    with path.open("r",encoding="utf-8") as f:
        for line in f:
            try: item=json.loads(line)
            except json.JSONDecodeError: item={"text":line.strip()}
            # Legacy/unscoped records are intentionally invisible to tenant queries.
            if not isinstance(item,dict) or str(item.get("workspace_id","")) != workspace_id:
                continue
            rendered=_text(item.get("text", item))
            score=sum(t in rendered.lower() for t in terms)
            if score: hits.append((score,rendered))
    hits.sort(key=lambda x:x[0],reverse=True)
    return {"state":"ok","plugin_id":"ai_memory","workspace_id":workspace_id,"results":[{"score":s,"text":t[:2000]} for s,t in hits[:5]]}

def _sandbox(action: str, p: dict) -> dict:
    if action!="run_tests": raise ValueError("unsupported_xparallel_sandbox_action")
    if p.get("human_approved") is not True: raise PermissionError("human_approval_required")
    from .v1_runner import run_project
    result=run_project({"files":p.get("files"),"test_command":p.get("test_command","python -m unittest discover -v")})
    return {"state":"ok" if result.get("status")=="success" else "failed","plugin_id":"xparallel_sandbox","result":result,"transfer":{"real_world_execution":"not_performed","production_deployment":"disabled","requires_human_review":True}}

ADAPTERS={"github":_github,"google_drive":_drive,"web_search":_web_search,"file_retrieval":_file_retrieval,"ai_memory":_memory,"xparallel_sandbox":_sandbox}

def plugin_catalog(sandbox_available: bool=False) -> dict[str,Any]:
    plugins=[]
    for item in PLUGIN_REGISTRY:
        plugin=dict(item); env=plugin.pop("credential_env")
        configured=bool(env and os.getenv(env,"").strip())
        ready=plugin["adapter"] in ADAPTERS
        if plugin["id"]=="xparallel_sandbox": ready=bool(sandbox_available)
        needs_path = {"file_retrieval":"XP_FILE_RETRIEVAL_ROOT","ai_memory":"XP_AI_MEMORY_PATH"}.get(plugin["id"])
        path_configured = bool(needs_path and os.getenv(needs_path, "").strip())
        if ready and (configured or not env) and (not needs_path or path_configured) and (plugin["id"] != "xparallel_sandbox" or sandbox_available): status="available"
        elif env and not configured: status="credentials_missing"
        elif needs_path and not path_configured: status="configuration_required"
        elif plugin["id"] == "xparallel_sandbox" and not sandbox_available: status="sandbox_unavailable"
        else: status="adapter_unavailable"
        plugin.update(configured=configured,status=status,can_execute=status=="available")
        plugins.append(plugin)
    return {"service":"Axaliai Universal AI Mixer","state":"partial" if any(x["can_execute"] for x in plugins) else "configured_required","plugins":plugins,"security":{"credentials_from_environment_only":True,"least_privilege":True,"approval_required_for_consequential_actions":True,"catalog_does_not_grant_execution_permission":True}}

def execute_plugin(plugin_id: str, action: str, payload: dict[str,Any], *, human_approved: bool=False) -> dict[str,Any]:
    item=next((x for x in PLUGIN_REGISTRY if x["id"]==plugin_id),None)
    if not item: return {"state":"plugin_not_found","plugin_id":plugin_id}
    adapter=ADAPTERS.get(item["adapter"])
    if not adapter: return {"state":"plugin_unavailable","plugin_id":plugin_id,"reason":"adapter_not_implemented","action":action}
    if item["approval_required"] and not human_approved: return {"state":"approval_required","plugin_id":plugin_id,"action":action}
    try:
        payload=dict(payload or {})
        if plugin_id=="xparallel_sandbox": payload["human_approved"]=human_approved
        result=adapter(action,payload)
        return {**result,"plugin_id":plugin_id}
    except PermissionError as exc: return {"state":"approval_required","plugin_id":plugin_id,"reason":str(exc),"action":action}
    except (ValueError,urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError) as exc:
        # Never return credentials, request headers, or full response bodies.
        return {"state":"plugin_error","plugin_id":plugin_id,"action":action,"error":str(exc)[:300]}

def retrieve_plugin_context(query: str, plugin_ids: list[str], *, allow_private: bool=False, workspace_id: str="") -> dict[str,Any]:
    """Run only explicitly selected read/retrieval actions and return bounded untrusted context."""
    outputs=[]; chunks=[]
    allowed_public={"web_search"}
    action_by_id={"web_search":"search","github":"search_repositories","google_drive":"search_files","file_retrieval":"list_files","ai_memory":"search"}
    for pid in list(dict.fromkeys(plugin_ids))[:5]:
        if pid=="xparallel_sandbox": outputs.append({"plugin_id":pid,"state":"not_run","reason":"sandbox_is_not_a_retrieval_plugin"}); continue
        if not allow_private and pid not in allowed_public:
            outputs.append({"plugin_id":pid,"state":"blocked","reason":"private_plugin_requires_authenticated_mixer"}); continue
        payload={"query":query}
        if pid=="ai_memory": payload["workspace_id"]=workspace_id
        result=execute_plugin(pid,action_by_id.get(pid,"search"),payload)
        outputs.append({"plugin_id":pid,"state":result.get("state"),"error":result.get("error"),"reason":result.get("reason")})
        if result.get("state")=="ok":
            safe={k:v for k,v in result.items() if k not in {"state"}}
            chunks.append(f"[Plugin {pid}; untrusted reference data]\n{_text(safe,5000)}")
    return {"context":"\n\n".join(chunks)[:15000],"results":outputs}
