"""OneAI roaming-service planner.

This module plans cross-service work without pretending that a connector is live.
Execution requires a separately implemented, authenticated connector and explicit
user approval for consequential actions.
"""
from __future__ import annotations

from typing import Any

SERVICE_CATALOG = {
    "web_research": {
        "name": "Web research",
        "examples": ["search", "research", "find", "compare", "latest"],
        "connector": "web_search",
        "status": "not_configured",
        "description": "Find and compare information from approved web sources.",
    },
    "files_and_knowledge": {
        "name": "Files and knowledge",
        "examples": ["file", "document", "pdf", "summarize", "knowledge", "report"],
        "connector": "file_search",
        "status": "not_configured",
        "description": "Search authorized files and prepare summaries or reports.",
    },
    "communication": {
        "name": "Communication",
        "examples": ["email", "message", "slack", "notify", "send", "contact"],
        "connector": "communications",
        "status": "not_configured",
        "description": "Draft communications; sending requires an approved connector and confirmation.",
    },
    "project_work": {
        "name": "Project and workflow tools",
        "examples": ["task", "project", "issue", "ticket", "calendar", "schedule"],
        "connector": "workflow_tools",
        "status": "not_configured",
        "description": "Coordinate tasks across authorized project and workflow systems.",
    },
    "software_build": {
        "name": "Software development",
        "examples": ["code", "build", "deploy", "test", "debug", "repository", "api"],
        "connector": "development_tools",
        "status": "not_configured",
        "description": "Inspect and propose code changes; deployment remains approval-gated.",
    },
    "business_operations": {
        "name": "Business operations",
        "examples": ["customer", "crm", "sales", "invoice", "order", "business"],
        "connector": "business_systems",
        "status": "not_configured",
        "description": "Plan work involving authorized customer and business systems.",
    },
}

ACTION_WORDS = {
    "send", "delete", "publish", "deploy", "purchase", "buy", "transfer",
    "invite", "modify", "update", "submit", "execute", "create account",
}


def plan_roaming(query: str) -> dict[str, Any]:
    """Return an explainable roaming plan; does not call external services."""
    goal = str(query or "").strip()
    if not goal:
        raise ValueError("query_required")
    if len(goal) > 12000:
        raise ValueError("query_too_large")

    lowered = goal.lower()
    selected = []
    for service_id, service in SERVICE_CATALOG.items():
        if any(word in lowered for word in service["examples"]):
            selected.append({
                "id": service_id,
                "name": service["name"],
                "connector": service["connector"],
                "connector_status": service["status"],
                "purpose": service["description"],
            })

    if not selected:
        selected = [{
            "id": "general_assistance",
            "name": "General assistance",
            "connector": None,
            "connector_status": "not_required_for_planning",
            "purpose": "Clarify the goal and identify any required authorized services.",
        }]

    approval_required = any(word in lowered for word in ACTION_WORDS)
    return {
        "service": "OneAI Roaming Services",
        "mode": "plan_only",
        "status": "planned",
        "goal": goal,
        "services": selected,
        "connector_count": len(selected),
        "configured_connector_count": sum(
            item["connector_status"] == "configured" for item in selected
        ),
        "approval_required": approval_required,
        "execution_performed": False,
        "next_steps": [
            "Configure only the connectors required for this task using server-side secrets.",
            "Validate connector permissions and scope before enabling access.",
            "Require user approval before consequential external changes.",
            "Execute through an isolated environment where applicable and return evidence.",
        ],
        "notice": (
            "This endpoint creates a plan only. It does not access external accounts, "
            "call third-party services, or execute actions."
        ),
    }
