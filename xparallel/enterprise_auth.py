"""Trusted identity adapter for enterprise user-facing API routes.

Identity is carried separately from XP_TOKEN: XP_TOKEN remains a machine/service
credential. The X-Enterprise-Identity token must be minted server-side only after
an upstream login adapter has authenticated the user and checked workspace membership.
"""
from __future__ import annotations

from typing import Mapping
from xparallel.authz import authorize
from xparallel.tenant_identity import IdentityError, verify_identity_token


def required_action(method: str, path: str) -> str | None:
    method = str(method or "").upper()
    path = str(path or "").split("?", 1)[0]
    if method == "GET":
        if path.startswith("/api/elle/tasks/") or path.startswith("/api/omni/records/") or path == "/api/omni/search":
            return "read"
    if method == "POST":
        if path == "/api/elle/tasks" or path.endswith("/transition") and path.startswith("/api/elle/tasks/"):
            return "create_solution"
        if path.startswith("/api/elle/tasks/") and path.endswith("/approve"):
            return "approve_deployment"
        if path.startswith("/api/elle/tasks/") and path.endswith("/verify"):
            return "verify"
        if path == "/api/omni/records":
            return "create_solution"
        if path == "/api/omni/search":
            return "read"
        if path.startswith("/api/omni/records/") and path.endswith("/verify"):
            return "verify"
        if path == "/api/parallel/research":
            return "create_solution"
        if path == "/api/xparallel/dispatch":
            return "approve_deployment"
    return None


def authorize_enterprise_request(headers: Mapping[str, str], method: str, path: str):
    """Return (trusted_context, error); ignore all client-supplied identity fields."""
    action = required_action(method, path)
    if action is None:
        return None, None
    token = headers.get("X-Enterprise-Identity", "")
    if not token:
        return None, "unauthorized"
    try:
        claims = verify_identity_token(token)
    except IdentityError:
        return None, "unauthorized"
    if not authorize(claims["role"], action):
        return None, "forbidden"
    return {
        "workspace_id": claims["workspace_id"],
        "actor": claims["actor"],
        "role": claims["role"],
    }, None
