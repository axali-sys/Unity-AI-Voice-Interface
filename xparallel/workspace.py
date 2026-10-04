"""Tenant/workspace boundary for XParallel V1."""
from __future__ import annotations
import hashlib
import re
from typing import Any

DEFAULT_WORKSPACE = "default"

def workspace_id(value: Any) -> str:
    raw = str(value or DEFAULT_WORKSPACE).strip()
    if not raw:
        return DEFAULT_WORKSPACE
    raw = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw)[:64].strip("-")
    return raw or DEFAULT_WORKSPACE

def workspace_fingerprint(workspace: str, actor: str = "human") -> str:
    return hashlib.sha256(f"{workspace_id(workspace)}:{actor}".encode()).hexdigest()

def workspace_context(data: dict[str, Any]) -> dict[str, str]:
    workspace = workspace_id(data.get("workspace_id"))
    actor = str(data.get("actor") or "human").strip()[:128] or "human"
    return {"workspace_id": workspace, "actor": actor,
            "workspace_fingerprint": workspace_fingerprint(workspace, actor)}
