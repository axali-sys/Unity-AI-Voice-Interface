"""Internet-wide OneAI roaming planner.

The planner is intentionally not restricted to predefined industry domains.
It creates an internet-wide discovery plan. Real browsing, authenticated service
access, and consequential actions require configured tools and explicit approval.
"""
from __future__ import annotations

from typing import Any

ACTION_WORDS = {
    "send", "delete", "publish", "deploy", "purchase", "buy", "transfer",
    "invite", "modify", "update", "submit", "execute", "create account",
    "book", "pay", "cancel", "post", "share", "change settings",
}


def plan_roaming(query: str) -> dict[str, Any]:
    """Return an internet-wide discovery plan; does not call external services."""
    goal = str(query or "").strip()
    if not goal:
        raise ValueError("query_required")
    if len(goal) > 12000:
        raise ValueError("query_too_large")

    lowered = goal.lower()
    approval_required = any(word in lowered for word in ACTION_WORDS)

    return {
        "service": "OneAI Roaming Services",
        "mode": "internet_wide_plan_only",
        "status": "planned",
        "scope": "internet_wide",
        "domain_restriction": False,
        "goal": goal,
        "discovery_strategy": {
            "approach": "goal_driven_dynamic_discovery",
            "description": (
                "Determine which websites, public information sources, APIs, "
                "online tools, platforms, or service endpoints can help with this "
                "specific goal. Select the route dynamically instead of restricting "
                "the task to a fixed industry or service category."
            ),
            "candidate_types": [
                "websites",
                "public_information_sources",
                "search_engines",
                "documentations_and_knowledge_sources",
                "APIs_and_integrations",
                "online_tools_and_platforms",
                "authorized_account_services",
            ],
            "selection_rule": (
                "Choose sources and tools based on relevance to the user's goal, "
                "availability, trustworthiness, permissions, and task requirements."
            ),
        },
        "configured_connector_count": 0,
        "approval_required": approval_required,
        "execution_performed": False,
        "next_steps": [
            "Discover relevant online sources and services for the goal at runtime.",
            "Use only browsing and connectors that are actually configured and available.",
            "Verify source identity, relevance, access permissions, and returned evidence.",
            "Request user approval before consequential external actions.",
            "Report completed, blocked, and unverified steps separately.",
        ],
        "notice": (
            "This endpoint creates a plan only. It does not browse the live internet, "
            "access external accounts, call third-party services, or execute actions. "
            "Internet-wide roaming requires working browsing/search tools and approved "
            "connectors; it is not yet enabled by this planner alone."
        ),
    }
