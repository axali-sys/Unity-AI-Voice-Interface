"""Billing contact and invoice-preview boundary. No payment capture occurs here."""
from __future__ import annotations
import os
from typing import Any

DEFAULT_CURRENCY = "USD"

def billing_profile(organization_id: str) -> dict[str, Any]:
    canonical = str(organization_id or "default").strip().lower()
    return {
        "organization_id": canonical,
        "email": os.getenv("XP_BILLING_EMAIL", ""),
        "currency": os.getenv("XP_BILLING_CURRENCY", DEFAULT_CURRENCY),
        "payment_status": "not_connected",
    }

def invoice_request(
    organization_id: str,
    events: list[dict[str, Any]],
    unit_price: float = 1.0,
) -> dict[str, Any]:
    profile = billing_profile(organization_id)
    target = profile["organization_id"]
    units = sum(
        int(e.get("units", 0))
        for e in events
        if str(e.get("workspace_id", "")).strip().lower() == target
    )
    return {
        **profile,
        "units": units,
        "unit_price": unit_price,
        "amount": round(units * unit_price, 2),
        "status": "invoice_preview",
    }
