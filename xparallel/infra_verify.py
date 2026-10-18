"""Read-only-by-default smoke checks for a deployed XParallel API.

Run:
  XP_BASE_URL=https://api.example.com python -m xparallel.infra_verify
  XP_TOKEN=... XP_PUBLIC_ORIGIN=https://app.example.com python -m xparallel.infra_verify --live-ai --live-roam

Provider calls and temporary memory writes are opt-in. Secrets are never printed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

def _request(base_url: str, path: str, *, token: str = "", origin: str = "",
             payload: dict[str, Any] | None = None, timeout: float = 12.0) -> tuple[int | None, dict[str, Any]]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if origin:
        headers["Origin"] = origin
    data = None
    method = "GET"
    if payload is not None:
        method = "POST"
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(base_url.rstrip("/") + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read(1_000_000).decode("utf-8", errors="replace")
            status = response.status
    except urllib.error.HTTPError as exc:
        status = exc.code
        raw = exc.read(8192).decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return None, {"error": "transport_error", "error_type": type(exc).__name__}
    try:
        parsed = json.loads(raw)
        return status, parsed if isinstance(parsed, dict) else {"response_type": type(parsed).__name__}
    except (json.JSONDecodeError, TypeError):
        return status, {"response_type": "non_json", "body_length": len(raw)}

def _record(results: list[dict[str, Any]], name: str, passed: bool | None,
            status: int | None, detail: str) -> None:
    state = "PASS" if passed is True else "FAIL" if passed is False else "SKIP"
    results.append({"check": name, "result": state, "http_status": status, "detail": detail})
    print(f"{state:4} {name}: HTTP {status if status is not None else 'no response'} — {detail}")

def _short(payload: dict[str, Any], *keys: str) -> str:
    bits = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)):
            bits.append(f"{key}={value}")
    return ", ".join(bits) or "JSON response received"

def run(args: argparse.Namespace) -> int:
    base_url = (args.base_url or os.getenv("XP_BASE_URL", "")).strip().rstrip("/")
    if not base_url.startswith("https://"):
        print("ERROR: set XP_BASE_URL to the HTTPS base URL of the API (not just the frontend URL).", file=sys.stderr)
        return 2
    token = os.getenv("XP_TOKEN", "").strip()
    origin = (args.origin or os.getenv("XP_PUBLIC_ORIGIN", "")).strip().rstrip("/")
    if not origin:
        origin = base_url
    results: list[dict[str, Any]] = []

    status, body = _request(base_url, "/health")
    _record(results, "runtime_health", status == 200 and body.get("status") == "ok",
            status, _short(body, "status", "network", "version", "sandbox_available"))

    for path, label in [
        ("/public/health", "public_health"),
        ("/public/system", "system_configuration"),
        ("/public/xparallel/access", "gateway_access_manifest"),
    ]:
        status, body = _request(base_url, path, origin=origin)
        ok = status == 200
        if label == "system_configuration" and ok:
            detail = _short(body, "status", "operational_status")
            mixer = body.get("mixer")
            roaming = body.get("roaming")
            if isinstance(mixer, dict):
                detail += f"; mixer_configured={mixer.get('configured', 'unknown')}"
            if isinstance(roaming, dict):
                detail += f"; roaming_status={roaming.get('status', 'unknown')}"
            detail += "; configuration is not proof of live provider operation"
        else:
            detail = _short(body, "status", "network", "version", "error")
        _record(results, label, ok, status, detail)

    status, body = _request(base_url, "/memory")
    _record(results, "unauthenticated_memory_denied",
            status == 401 and body.get("error") == "unauthorized", status,
            "expected HTTP 401 without a bearer token" if status == 401 else _short(body, "error"))

    if not token:
        for name in ("authenticated_memory_access", "execution_approval_gate"):
            _record(results, name, None, None, "set XP_TOKEN to run authenticated checks")
    else:
        status, body = _request(base_url, "/memory", token=token)
        _record(results, "authenticated_memory_access", status == 200 and isinstance(body.get("memories"), list),
                status, _short(body, "error"))

        # This intentionally omits X-XParallel-Approval. A correct server rejects the
        # request before execution; the probe is not authorized to run the supplied file.
        probe = {"query": "infrastructure approval-gate smoke check",
                 "execution": {"files": [{"path": "smoke.txt", "content": "approval gate probe only"}]}}
        status, body = _request(base_url, "/execute", token=token, payload=probe)
        _record(results, "execution_approval_gate",
                status == 403 and body.get("error") == "human_approval_required", status,
                "expected approval denial before execution" if status == 403 else _short(body, "error"))

        if args.write_memory:
            marker = f"xparallel-infra-smoke-{int(time.time())}"
            workspace = "infra-smoke"
            status, saved = _request(base_url, "/memory/save", token=token, payload={
                "content": marker, "summary": "Temporary infrastructure smoke test", "tags": ["smoke"],
                "workspace_id": workspace,
            })
            memory_id = saved.get("id")
            _record(results, "memory_write", status in (200, 201) and bool(memory_id), status,
                    "temporary record created" if memory_id else _short(saved, "error"))
            if memory_id:
                status, found = _request(base_url, "/memory/search", token=token, payload={
                    "query": marker, "limit": 5, "workspace_id": workspace,
                })
                memories = found.get("memories", [])
                hit = isinstance(memories, list) and any(item.get("id") == memory_id for item in memories if isinstance(item, dict))
                _record(results, "memory_retrieval", status == 200 and hit, status,
                        "saved record was retrieved" if hit else "saved record not found in search results")
                status, deleted = _request(base_url, "/memory/forget", token=token, payload={
                    "id": memory_id, "workspace_id": workspace,
                })
                _record(results, "memory_cleanup", status == 200 and deleted.get("deleted") is True, status,
                        "temporary record removed" if deleted.get("deleted") is True else _short(deleted, "error", "deleted"))

        if args.live_ai:
            status, body = _request(base_url, "/chat", token=token, payload={
                "messages": [{"role": "user", "content": "Reply with the exact word: XPARALLEL_SMOKE_OK"}],
                "use_memory": False, "workspace_id": "infra-smoke",
            }, timeout=45)
            mixer = body.get("mixer") if isinstance(body.get("mixer"), dict) else {}
            state = mixer.get("state", "not_reported")
            ok = status == 200 and isinstance(body.get("answer"), str) and bool(body.get("answer", "").strip())
            _record(results, "live_ai_mixer_call", ok, status,
                    f"mixer_state={state}; provider credentials and model IDs are tested only when this option is used")

        if args.live_roam:
            status, body = _request(base_url, "/public/roam", token=token, origin=origin,
                                    payload={"query": "XParallel AI infrastructure", "workspace_id": "infra-smoke"},
                                    timeout=45)
            ok = status == 200 and body.get("status") == "success"
            _record(results, "live_roaming_search", ok, status,
                    _short(body, "status", "error", "provider"))

    failures = sum(item["result"] == "FAIL" for item in results)
    skips = sum(item["result"] == "SKIP" for item in results)
    print(json.dumps({"base_url": base_url, "checks": results, "failed": failures, "skipped": skips}, indent=2))
    return 1 if failures else 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Verify XParallel API infrastructure with evidence-based HTTP smoke checks.")
    parser.add_argument("--base-url", default="", help="HTTPS API base URL; defaults to XP_BASE_URL")
    parser.add_argument("--origin", default="", help="Configured frontend origin; defaults to XP_PUBLIC_ORIGIN or base URL")
    parser.add_argument("--write-memory", action="store_true", help="Create, retrieve, then delete a temporary memory record")
    parser.add_argument("--live-ai", action="store_true", help="Make a real provider-backed /chat call (may incur cost)")
    parser.add_argument("--live-roam", action="store_true", help="Make a real roaming search call (may incur cost)")
    return run(parser.parse_args())

if __name__ == "__main__":
    raise SystemExit(main())
