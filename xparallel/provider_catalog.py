"""Environment-backed provider catalog for OneAI's hybrid Free Access Hub.

This module reports configuration only. It does not probe provider health or
free-tier quotas, and never returns API keys or endpoint URLs to clients.
"""
import os
from .free_access_hub import Provider


def configured_providers(environ=None) -> list[Provider]:
    env = os.environ if environ is None else environ
    providers = []

    # Local inference is configured only when both the runtime URL and model
    # are explicitly supplied. Status remains unknown until health is probed.
    if env.get("XP_HUB_LOCAL_URL", "").strip() and env.get("XP_HUB_LOCAL_MODEL", "").strip():
        providers.append(Provider(
            id="local-ollama", kind="local",
            capabilities=("chat", "writing", "coding", "reasoning"),
            status="unknown", estimated_cost_usd=0.0, configured=True,
        ))

    free_id = env.get("XP_HUB_FREE_PROVIDER_ID", "").strip()
    free_model = env.get("XP_HUB_FREE_PROVIDER_MODEL", "").strip()
    free_key = env.get("XP_HUB_FREE_PROVIDER_API_KEY", "").strip()
    if free_id and free_model and free_key:
        providers.append(Provider(
            id=free_id, kind="free_cloud",
            capabilities=("chat", "writing", "coding", "reasoning"),
            status="unknown", estimated_cost_usd=0.0, configured=True,
        ))

    paid_id = env.get("XP_HUB_PAID_PROVIDER_ID", "").strip()
    paid_model = env.get("XP_HUB_PAID_PROVIDER_MODEL", "").strip()
    paid_key = env.get("XP_HUB_PAID_PROVIDER_API_KEY", "").strip()
    try:
        paid_cost = float(env.get("XP_HUB_PAID_ESTIMATED_COST_USD", ""))
    except (TypeError, ValueError):
        paid_cost = -1.0
    if paid_id and paid_model and paid_key and paid_cost >= 0:
        providers.append(Provider(
            id=paid_id, kind="paid",
            capabilities=("chat", "writing", "coding", "reasoning"),
            status="unknown", estimated_cost_usd=paid_cost,
            requires_approval=True, configured=True,
        ))
    return providers
