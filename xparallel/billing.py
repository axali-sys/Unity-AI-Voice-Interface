"""Billing foundation: metered usage records, not payment collection."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

EVENT_UNITS = {"solution_created": 1, "verification": 1, "graph_search": 1,
               "sandbox_run": 5, "deployment_approved": 10}

def usage_event(event: str, workspace_id: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if event not in EVENT_UNITS:
        raise ValueError("unknown_billing_event")
    return {"event_id": f"{workspace_id}:{event}:{datetime.now(timezone.utc).timestamp()}",
            "event": event, "workspace_id": workspace_id,
            "units": EVENT_UNITS[event], "created_at": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}}

def invoice_preview(workspace_id: str, events: list[dict[str, Any]], unit_price: float = 1.0) -> dict[str, Any]:
    selected = [e for e in events if e.get("workspace_id") == workspace_id]
    units = sum(int(e.get("units", 0)) for e in selected)
    return {"workspace_id": workspace_id, "events": len(selected), "units": units,
            "unit_price": unit_price, "estimated_total": round(units * unit_price, 2),
            "currency": "USD", "status": "preview"}
