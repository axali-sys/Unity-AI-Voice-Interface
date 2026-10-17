"""Provider-neutral live roaming engine for OneAI."""
from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from urllib.parse import urlparse

TIMEOUT = 12
MAX_QUERY = 12000
MAX_RESULTS = 8

def _post(url, payload, token=None):
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("configured_endpoint_must_use_https")
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "OneAI-Roaming/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise RuntimeError("provider_response_too_large")
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("provider_invalid_response")
    return data

def _workers():
    raw = os.getenv("ONEAI_ROAMING_WORKERS", "").strip()
    if not raw:
        return [], []
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return [], [{"provider":"remote_workers","reason":"invalid_worker_json"}]
    if not isinstance(entries, list):
        return [], [{"provider":"remote_workers","reason":"worker_config_must_be_array"}]
    valid, skipped = [], []
    for i, item in enumerate(entries):
        if not isinstance(item, dict):
            skipped.append({"provider":f"worker_{i}","reason":"worker_config_must_be_object"}); continue
        name, url, token = item.get("name", f"worker_{i}"), item.get("url"), item.get("token")
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme != "https" or not parsed.hostname or not isinstance(token, str) or not token:
            skipped.append({"provider":str(name),"reason":"worker_requires_https_url_and_token"}); continue
        valid.append({"name":str(name),"url":url.rstrip("/"),"token":token})
    return valid, skipped

def roam(query):
    goal = str(query or "").strip()
    if not goal:
        raise ValueError("query_required")
    if len(goal) > MAX_QUERY:
        raise ValueError("query_too_large")
    lowered = goal.lower()
    approval = any(word in lowered for word in ("send","delete","publish","deploy","purchase","buy","transfer","invite","modify","update","submit","execute","book","pay","cancel","post","share"))
    providers, skipped, sources, answers = [], [], [], []
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if key:
        started = time.monotonic()
        try:
            data = _post("https://api.tavily.com/search", {"api_key":key,"query":goal,"search_depth":"basic","max_results":MAX_RESULTS,"include_answer":True,"include_raw_content":False})
            providers.append({"provider":"tavily","status":"success","latency_ms":round((time.monotonic()-started)*1000)})
            if isinstance(data.get("answer"), str) and data["answer"].strip():
                answers.append(data["answer"][:8000])
            for item in data.get("results",[])[:MAX_RESULTS]:
                if isinstance(item,dict) and isinstance(item.get("url"),str) and item["url"].startswith("https://"):
                    sources.append({"title":str(item.get("title") or item["url"])[:500],"url":item["url"][:2000],"snippet":str(item.get("content") or "")[:4000],"provider":"tavily"})
        except Exception as exc:
            skipped.append({"provider":"tavily","reason":str(exc)[:300]})
    else:
        skipped.append({"provider":"tavily","reason":"TAVILY_API_KEY_not_configured"})
    workers, config_errors = _workers()
    skipped.extend(config_errors)
    for worker in workers:
        started = time.monotonic()
        try:
            data = _post(worker["url"]+"/v1/roam",{"query":goal,"scope":"internet_wide","approval_required":approval},worker["token"])
            providers.append({"provider":"remote_worker","worker":worker["name"],"status":"success","latency_ms":round((time.monotonic()-started)*1000)})
            answer = data.get("answer")
            if isinstance(answer,str) and answer.strip(): answers.append(answer[:8000])
            for item in data.get("sources",[])[:MAX_RESULTS]:
                if isinstance(item,dict) and isinstance(item.get("url"),str) and item["url"].startswith("https://"):
                    sources.append({"title":str(item.get("title") or item["url"])[:500],"url":item["url"][:2000],"snippet":str(item.get("snippet") or "")[:4000],"provider":worker["name"]})
        except Exception as exc:
            skipped.append({"provider":"worker:"+worker["name"],"reason":str(exc)[:300]})
    success = bool(sources or answers)
    return {
        "service":"OneAI Roaming Engine","mode":"internet_wide_roaming",
        "status":"success" if success else "roaming_unavailable",
        "scope":"internet_wide","domain_restriction":False,"goal":goal,
        "approval_required":approval,"execution_performed":bool(providers),
        "providers":providers,"skipped_providers":skipped,"sources":sources[:MAX_RESULTS*(len(workers)+1)],
        "answer":"\n\n".join(answers),"configured_worker_count":len(workers),
        "notice":"Only results from listed configured providers are live evidence. The engine can use independent HTTPS worker services and is not tied to one worker/server. Search does not perform account actions; consequential actions require authorized connectors and explicit approval.",
        "setup":[] if success else ["Set TAVILY_API_KEY as a server-side secret for live web search.","Optionally set ONEAI_ROAMING_WORKERS to a JSON array of trusted HTTPS workers with name, url, and token.","Each remote worker must implement POST /v1/roam and return JSON with optional answer and sources fields.","Never commit credentials to source control."]
    }
