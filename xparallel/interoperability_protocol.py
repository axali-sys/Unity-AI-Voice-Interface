"""XParallel interoperability contracts over the authenticated roaming registry."""
from __future__ import annotations
from xparallel.roaming_registry import discover, enqueue_task

PROTOCOL_VERSION = "1.0"
ALLOWED_TASK_TYPES = {"chat", "text.transform", "knowledge.lookup", "diagnostic"}

def agent_passport(runtime):
    """Return a public capability passport; never expose credentials."""
    return {
        "protocol": "XParallel-Interop",
        "protocol_version": PROTOCOL_VERSION,
        "agent_id": runtime.get("runtime_id"),
        "display_name": runtime.get("name"),
        "endpoint": runtime.get("base_url"),
        "capabilities": runtime.get("capabilities", []),
        "status": runtime.get("status"),
        "last_seen": runtime.get("last_seen"),
        "expires_at": runtime.get("expires_at"),
        "credential_disclosed": False,
    }

def discover_agents(capability=None, limit=20):
    return [agent_passport(x) for x in discover(capability, limit)]

def dispatch_approved_task(runtime_id, task_type, payload, workspace_id, *, approved):
    if not approved:
        raise PermissionError("human_approval_required")
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError("task_type_not_allowlisted")
    return enqueue_task(runtime_id, task_type, payload, workspace_id)
