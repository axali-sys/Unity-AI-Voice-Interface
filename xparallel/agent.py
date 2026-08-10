"""XParallel v0.5 execution-agent boundary.

The agent validates and plans an operation. It does not execute arbitrary code.
"""
from .router import route

ALLOWED_ACTIONS = {"search", "retrieve", "build_plan"}


def plan(query: str) -> dict:
    decision = route(query)
    action = "build_plan" if decision["mode"] == "build" else "retrieve"
    return {
        "agent": "xparallel-execution-agent",
        "status": "planned",
        "mode": decision["mode"],
        "action": action,
        "resources": decision["resources"],
        "requires_approval": action == "build_plan",
    }
