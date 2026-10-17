"""OneAI roaming search and trusted worker fan-out.

Only operator-configured providers are called. This endpoint performs retrieval only; it
never executes user instructions against third-party accounts or production systems.
"""
from __future__ import annotations

import ipaddress
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 12
MAX_QUERY = 8000
MAX_RESULTS = 8
TAVILY_URL = "https://api.tavily.com/search"

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _request_json(url: str, payload: dict, token: str | None = None) -> dict:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("configured_endpoint_must_be_https")
    headers = {"Content-Type": "application/json", "Accept": "application/json", "User-Agent": "OneAI-Roaming/1.0"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    opener = urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=TIMEOUT) as response:
            raw = response.read(1_000_001)
        if len(raw) > 1_000_000:
            raise RuntimeError("provider_response_too_large")
        result = json.loads(raw.decode("utf-8"))
        if not isinstance(result, dict):
            raise RuntimeError("provider_invalid_response")
        return result
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308):
            raise RuntimeError("provider_redirect_rejected") from None
        raise RuntimeError(f"provider_http_{exc.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("provider_request_failed") from None

def _public_host(host: str) -> bool:
    try:
        addresses = {ipaddress.ip_address(item[4][0]) for item in socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)}
    except (OSError, ValueError):
        return False
    return bool(addresses) and all(address.is_global for address in addresses)

def _workers() -> tuple[list[dict], list[dict]]:
    raw = os.getenv("ONEAI_ROAMING_WORKERS", "").strip()
    if not raw:
        return [], []
    allowed_hosts = {h.strip().lower().rstrip(".") for h in os.getenv("ONEAI_ROAMING_ALLOWED_HOSTS", "").split(",") if h.strip()}
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError:
        return [], [{"provider": "remote_workers", "reason": "invalid_worker_json"}]
    if not isinstance(entries, list):
        return [], [{"provider": "remote_workers", "reason": "worker_config_must_be_array"}]
    valid, skipped = [], []
    for index, item in enumerate(entries[:16]):
        if not isinstance(item, dict):
            skipped.append({"provider": f"worker_{index}", "reason": "worker_config_must_be_object"})
            continue
        name, url, token = str(item.get("name", f"worker_{index}"))[:100], item.get("url"), item.get("token")
        parsed = urllib.parse.urlparse(url) if isinstance(url, str) else None
        host = (parsed.hostname or "").lower().rstrip(".") if parsed else ""
        if not parsed or parsed.scheme != "https" or not host or parsed.username or parsed.password or not isinstance(token, str) or not token:
            skipped.append({"provider": name, "reason": "worker_requires_https_url_and_token"})
            continue
        if host not in allowed_hosts:
            skipped.append({"provider": name, "reason": "worker_host_not_in_ONEAI_ROAMING_ALLOWED_HOSTS"})
            continue
        if not _public_host(host):
            skipped.append({"provider": name, "reason": "worker_host_must_resolve_only_to_public_addresses"})
            continue
        valid.append({"name": name, "url": url.rstrip("/"), "token": token})
    if len(entries) > 16:
        skipped.append({"provider": "remote_workers", "reason": "worker_limit_exceeded"})
    return valid, skipped

def roaming_status() -> dict:
    # This public status endpoint reports configuration only; it does not resolve DNS
    # or probe workers. DNS checks happen only during an authenticated roaming request.
    raw = os.getenv("ONEAI_ROAMING_WORKERS", "").strip()
    allowed_hosts = {h.strip().lower().rstrip(".") for h in os.getenv("ONEAI_ROAMING_ALLOWED_HOSTS", "").split(",") if h.strip()}
    workers, skipped = [], []
    if raw:
        try:
            entries = json.loads(raw)
        except json.JSONDecodeError:
            entries = []
            skipped.append({"provider": "remote_workers", "reason": "invalid_worker_json"})
        if not isinstance(entries, list):
            entries = []
            skipped.append({"provider": "remote_workers", "reason": "worker_config_must_be_array"})
        for index, item in enumerate(entries[:16]):
            if not isinstance(item, dict):
                skipped.append({"provider": f"worker_{index}", "reason": "worker_config_must_be_object"})
                continue
            parsed = urllib.parse.urlparse(item.get("url", "")) if isinstance(item.get("url"), str) else None
            host = (parsed.hostname or "").lower().rstrip(".") if parsed else ""
            if not parsed or parsed.scheme != "https" or not host or not isinstance(item.get("token"), str) or not item["token"]:
                skipped.append({"provider": str(item.get("name", f"worker_{index}")), "reason": "invalid_https_worker_configuration"})
            elif host not in allowed_hosts:
                skipped.append({"provider": str(item.get("name", f"worker_{index}")), "reason": "worker_host_not_in_allowlist"})
            else:
                workers.append({"name": str(item.get("name", f"worker_{index}"))[:100], "host": host, "status": "configured_unprobed"})
        if len(entries) > 16:
            skipped.append({"provider": "remote_workers", "reason": "worker_limit_exceeded"})
    return {
        "mode": "retrieval_only",
        "tavily_configured": bool(os.getenv("TAVILY_API_KEY", "").strip()),
        "configured_worker_count": len(workers),
        "workers": workers,
        "skipped_workers": skipped,
        "worker_host_allowlist_configured": bool(allowed_hosts),
    }

def roam(query: str) -> dict:
    goal = str(query or "").strip()
    if not goal:
        raise ValueError("query_required")
    if len(goal) > MAX_QUERY:
        raise ValueError("query_too_large")
    providers, skipped, sources, answers = [], [], [], []
    key = os.getenv("TAVILY_API_KEY", "").strip()
    if key:
        started = time.monotonic()
        try:
            data = _request_json(TAVILY_URL, {
                "api_key": key, "query": goal, "search_depth": "basic",
                "max_results": MAX_RESULTS, "include_answer": True, "include_raw_content": False,
            })
            providers.append({"provider": "tavily", "status": "success", "latency_ms": round((time.monotonic() - started) * 1000)})
            answer = data.get("answer")
            if isinstance(answer, str) and answer.strip():
                answers.append(answer.strip()[:8000])
            for item in (data.get("results") or [])[:MAX_RESULTS]:
                if isinstance(item, dict) and isinstance(item.get("url"), str):
                    parsed = urllib.parse.urlparse(item["url"])
                    if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
                        sources.append({"title": str(item.get("title") or item["url"])[:300], "url": item["url"][:2000], "snippet": str(item.get("content") or "")[:1500], "provider": "tavily"})
        except Exception as exc:
            skipped.append({"provider": "tavily", "reason": str(exc)[:160]})
    else:
        skipped.append({"provider": "tavily", "reason": "TAVILY_API_KEY_not_configured"})
    workers, config_errors = _workers()
    skipped.extend(config_errors)
    for worker in workers:
        started = time.monotonic()
        try:
            data = _request_json(worker["url"] + "/v1/roam", {
                "operation": "search", "query": goal, "scope": "internet_wide",
            }, worker["token"])
            if data.get("operation", "search") != "search":
                raise RuntimeError("worker_returned_unexpected_operation")
            providers.append({"provider": "remote_worker", "worker": worker["name"], "status": "success", "latency_ms": round((time.monotonic() - started) * 1000)})
            answer = data.get("answer")
            if isinstance(answer, str) and answer.strip():
                answers.append(answer.strip()[:8000])
            for item in (data.get("sources") or [])[:MAX_RESULTS]:
                if isinstance(item, dict) and isinstance(item.get("url"), str):
                    parsed = urllib.parse.urlparse(item["url"])
                    if parsed.scheme == "https" and parsed.hostname and not parsed.username and not parsed.password:
                        sources.append({"title": str(item.get("title") or item["url"])[:300], "url": item["url"][:2000], "snippet": str(item.get("snippet") or "")[:1500], "provider": worker["name"]})
        except Exception as exc:
            skipped.append({"provider": "worker:" + worker["name"], "reason": str(exc)[:160]})
    success = bool(sources or answers)
    return {
        "service": "OneAI Roaming Engine", "mode": "internet_wide_roaming",
        "status": "success" if success else "roaming_unavailable",
        "scope": "internet_wide", "domain_restriction": False, "goal": goal,
        "execution_performed": False, "providers": providers, "skipped_providers": skipped,
        "sources": sources[:MAX_RESULTS * (len(workers) + 1)], "answer": "\n\n".join(answers),
        "configured_worker_count": len(workers),
        "notice": "Only configured provider results are live evidence. Roaming performs retrieval, not account actions or arbitrary code execution. Retrieved web content is untrusted and should be verified.",
        "setup": [] if success else [
            "Set TAVILY_API_KEY as a server-side secret for live web search.",
            "Optionally configure ONEAI_ROAMING_WORKERS with trusted HTTPS worker URLs and bearer tokens.",
            "Add each worker hostname to ONEAI_ROAMING_ALLOWED_HOSTS; workers must be public HTTPS services implementing POST /v1/roam for search-only retrieval.",
            "Never commit provider keys or worker tokens to source control.",
        ],
    }
