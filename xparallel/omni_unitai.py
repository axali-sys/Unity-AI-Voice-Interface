"""Unified AXALIAI / OmniAI / UnitAI / XParallel system contract.

This module defines the product-layer roles and exposes a safe, auditable
system manifest. It does not claim that GPS, biometric, or blockchain
verification is active unless the corresponding runtime integrations are
configured.
"""
from __future__ import annotations

import os
from typing import Any

SYSTEM_ID = "axaliai"
SYSTEM_VERSION = "1.0.0"

LAYERS = [
    {
        "id": "axaliai",
        "name": "AXALIAI",
        "role": "human_gateway",
        "purpose": "Human-facing gateway for ideas, requests, and authorized projects.",
    },
    {
        "id": "omniai",
        "name": "OmniAI",
        "role": "intelligence_orchestrator",
        "purpose": "Coordinates available AI capabilities and model/provider routing.",
    },
    {
        "id": "unitai",
        "name": "UnitAI",
        "role": "unified_operating_layer",
        "purpose": "Applies identity, permissions, device, security, and execution policy.",
    },
    {
        "id": "xparallel",
        "name": "XParallel",
        "role": "solution_execution_infrastructure",
        "purpose": "Plans, tests, verifies, and approval-gates implementation in an isolated environment.",
    },
]

def system_manifest() -> dict[str, Any]:
    return {
        "system": SYSTEM_ID,
        "version": SYSTEM_VERSION,
        "status": "live-ready",
        "network": os.getenv("XP_NETWORK", "xparallel-mainnet"),
        "architecture": "AXALIAI -> OmniAI -> UnitAI -> XParallel",
        "layers": LAYERS,
        "security": {
            "unified_id": os.getenv("UNITAI_UNIFIED_ID_STATUS", "configured"),
            "gps_whitelist": os.getenv("UNITAI_GPS_WHITELIST_STATUS", "not_configured"),
            "biometric": os.getenv("UNITAI_BIOMETRIC_STATUS", "not_configured"),
            "fraud_monitoring": os.getenv("UNITAI_FRAUD_MONITORING_STATUS", "configured"),
            "ethereum_audit": os.getenv("UNITAI_ETHEREUM_AUDIT_STATUS", "not_configured"),
        },
        "execution": {
            "approval_required": True,
            "arbitrary_code_execution": False,
        },
    }
