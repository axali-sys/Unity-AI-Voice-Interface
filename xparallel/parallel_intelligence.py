"""Honest collaborative-reasoning coordinator using configured OneAI providers.

The current provider catalogue exposes configuration metadata, not a generic
multi-provider invocation contract. This module therefore reports whether a
real multi-provider run is possible and delegates planning to the existing
provider-backed planner without pretending one model is a panel.
"""
from __future__ import annotations
from xparallel.provider_catalog import configured_providers
from xparallel.parallel_world import create_parallel_plan

def capability_status():
    providers = configured_providers()
    usable = [p for p in providers if getattr(p, "configured", False)]
    return {
        "configured_provider_count": len(usable),
        "providers": [{"id": p.id, "kind": p.kind, "status": p.status,
                       "capabilities": list(p.capabilities)} for p in usable],
        "multi_model_consensus_available": False,
        "reason": ("A provider invocation adapter with independent model calls and "
                   "response comparison is not yet present." if len(usable) < 2 else
                   "Multiple providers are configured, but generic invocation and "
                   "consensus evaluation are not yet implemented."),
    }

def research(query, workspace_id="default"):
    status = capability_status()
    result = create_parallel_plan(query, workspace_id)
    return {
        "mode": "single_provider_plan",
        "collaboration_status": "not_available",
        "capability_status": status,
        "plan": result.get("plan"),
        "execution_performed": False,
        "verified": False,
    }
