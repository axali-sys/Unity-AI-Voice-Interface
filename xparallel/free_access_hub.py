"""Cost-aware provider selection for OneAI's hybrid Free Access Hub.

This module performs policy-based selection only. It does not call providers,
claim live quota status, bypass access controls, or incur charges.
"""
from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Iterable, Literal

ProviderKind = Literal["local", "free_cloud", "paid"]
ProviderStatus = Literal["available", "unavailable", "unknown"]

@dataclass(frozen=True)
class Provider:
    id: str
    kind: ProviderKind
    capabilities: tuple[str, ...]
    status: ProviderStatus = "unknown"
    estimated_cost_usd: float = 0.0
    requires_approval: bool = False
    configured: bool = False

    def public_record(self) -> dict:
        """Return safe, non-secret provider metadata for UI/API responses."""
        return asdict(self)

@dataclass(frozen=True)
class RouteDecision:
    status: Literal["selected", "needs_configuration", "no_eligible_provider"]
    provider_id: str | None
    reason: str
    estimated_cost_usd: float | None
    requires_approval: bool
    alternatives: tuple[str, ...] = ()

def select_provider(task: str, providers: Iterable[Provider], *,
                    allow_paid: bool = False,
                    paid_approval_granted: bool = False) -> RouteDecision:
    """Choose a suitable provider with local/free-first and paid-call guardrails."""
    capability = task.strip().lower()
    if not capability:
        return RouteDecision("no_eligible_provider", None,
                             "A task capability is required.", None, False)
    candidates = list(providers)
    eligible = [
        p for p in candidates
        if capability in {c.lower() for c in p.capabilities}
        and p.status == "available" and p.configured
        and p.estimated_cost_usd >= 0
        and (p.kind != "paid" or
             (allow_paid and paid_approval_granted and p.requires_approval))
    ]
    rank = {"local": 0, "free_cloud": 1, "paid": 2}
    eligible.sort(key=lambda p: (rank[p.kind], p.estimated_cost_usd, p.id))
    if eligible:
        chosen = eligible[0]
        return RouteDecision("selected", chosen.id,
            f"Selected an available, configured {chosen.kind} provider for {capability}.",
            chosen.estimated_cost_usd, chosen.requires_approval,
            tuple(p.id for p in eligible[1:]))
    matching = [p for p in candidates if capability in {c.lower() for c in p.capabilities}]
    if any(p.kind == "paid" and p.status == "available" and p.configured for p in matching):
        return RouteDecision("needs_configuration", None,
            "A paid provider may be available, but paid routing requires explicit enablement and approval.",
            None, True)
    if any(p.status == "unknown" for p in matching):
        return RouteDecision("needs_configuration", None,
            "Provider availability is unknown. Verify configuration and free quota before routing.",
            None, False)
    return RouteDecision("no_eligible_provider", None,
        "No configured, available provider supports this task. No paid request was made.",
        None, False)

def provider_directory(providers: Iterable[Provider]) -> list[dict]:
    """Expose provider metadata without secrets or unsupported live claims."""
    return [p.public_record() for p in providers]
