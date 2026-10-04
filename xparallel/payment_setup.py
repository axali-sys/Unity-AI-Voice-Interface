"""Payment destination setup for XParallel billing.

This module records a non-sensitive payout destination reference and billing
contact. It deliberately does not store bank account numbers, PINs, card data,
API secrets, or payment credentials.
"""
from __future__ import annotations

import os
from typing import Any

PROVIDER = "Ecobank"
ACCOUNT_MASK = "****2251"


def payment_setup(organization_id: str) -> dict[str, Any]:
    return {
        "organization_id": organization_id,
        "provider": os.getenv("XP_PAYOUT_PROVIDER", PROVIDER),
        "destination_type": "bank_account",
        "account_last4": ACCOUNT_MASK[-4:],
        "account_display": ACCOUNT_MASK,
        "billing_email": os.getenv("XP_BILLING_EMAIL", ""),
        "currency": os.getenv("XP_BILLING_CURRENCY", "USD"),
        "status": "manual_verification_required",
        "payment_capture": "disabled",
    }


def payment_request(
    organization_id: str,
    amount: float,
    currency: str = "USD",
    reference: str = "",
) -> dict[str, Any]:
    if amount <= 0:
        raise ValueError("amount_must_be_positive")
    setup = payment_setup(organization_id)
    return {
        **setup,
        "amount": round(float(amount), 2),
        "currency": currency.upper(),
        "reference": reference,
        "status": "payment_request_pending",
        "authorization_required": True,
    }
