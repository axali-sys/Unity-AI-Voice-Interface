"""Axaliai to XParallel access contract."""
from __future__ import annotations
import os
from typing import Any

GATEWAY_ID = "axaliai"
GATEWAY_VERSION = "1.0.0"
CAPABILITIES = ("ask", "route", "build", "solution", "verify", "graph_search", "system_manifest")

def gateway_manifest() -> dict[str, Any]:
    origins = [v.strip().rstrip("/") for v in os.getenv("XP_PUBLIC_ORIGINS", "https://axaliai.com,https://www.axaliai.com").split(",") if v.strip()]
    return {"gateway": GATEWAY_ID, "version": GATEWAY_VERSION, "network": os.getenv("XP_NETWORK", "xparallel-mainnet"), "status": "ready", "architecture": "AXALIAI -> OmniAI -> UnitAI -> XParallel", "access_model": "axaliai_gateway", "origins": origins, "capabilities": list(CAPABILITIES), "execution": "human_approval_required", "payment_capture": "disabled", "browser_secret_required": False}
