"""Read-only XParallel tokenomics proposal model.

This module contains scenario data only. It does not issue tokens, connect to a
blockchain, create wallets, set prices, or enable governance/transfer features.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation

MAX_SUPPLY = 1_000_000_000
ASSUMED_PRICE_USD = Decimal("1.00")

PROPOSAL_STATUS = "proposal_only"
ISSUED_SUPPLY = 0
CIRCULATING_SUPPLY = 0
MARKET_PRICE_USD = None
TOKEN_CONTRACT_DEPLOYED = False
TRANSFERS_ENABLED = False

_ALLOCATIONS = (
    {"key": "founders", "label": "Founders", "units": 500_000_000, "basis_points": 5000,
     "purpose": "Long-term creation and leadership; subject to vesting."},
    {"key": "ecosystem_treasury", "label": "Ecosystem treasury", "units": 200_000_000, "basis_points": 2000,
     "purpose": "Grants, integrations, infrastructure, and research."},
    {"key": "community_adoption", "label": "Community and adoption", "units": 120_000_000, "basis_points": 1200,
     "purpose": "Transparent participation programs."},
    {"key": "contributors", "label": "Contributors and developers", "units": 80_000_000, "basis_points": 800,
     "purpose": "Approved work, tools, and maintenance."},
    {"key": "strategic_partnerships", "label": "Strategic partnerships", "units": 50_000_000, "basis_points": 500,
     "purpose": "Milestone-based ecosystem collaborations."},
    {"key": "security_liquidity_reserve", "label": "Security and liquidity reserve", "units": 50_000_000, "basis_points": 500,
     "purpose": "Audits and incident response; liquidity use requires separate approval."},
)

CIRCULATION_CEILINGS = (
    {"period": "launch", "units": 30_000_000},
    {"period": "year_1", "units": 80_000_000},
    {"period": "year_2", "units": 180_000_000},
    {"period": "year_3", "units": 300_000_000},
    {"period": "year_4", "units": 450_000_000},
    {"period": "year_5", "units": 600_000_000},
)

VESTING = {
    "founders": {"cliff_months": 12, "vesting_months_after_cliff": 48,
                 "monthly_units_after_cliff": 10_416_666.6667},
    "contributors": {"cliff_months": 12, "vesting_months_after_cliff": 36},
    "ecosystem_treasury": {"release": "approved budgets and milestones"},
    "community_adoption": {"release": "gradual, eligibility-based"},
    "strategic_partnerships": {"release": "milestone-based with conflict review"},
    "security_liquidity_reserve": {"release": "locked initially; documented approval required"},
}


def get_tokenomics_proposal():
    """Return a defensive copy of the proposal; this is not live token state."""
    allocations = deepcopy(list(_ALLOCATIONS))
    return {
        "status": PROPOSAL_STATUS,
        "name": "XParallel",
        "purpose": ["governance", "ecosystem_participation"],
        "maximum_supply": MAX_SUPPLY,
        "assumed_price_usd": str(ASSUMED_PRICE_USD),
        "hypothetical_fully_diluted_valuation_usd": str(
            Decimal(MAX_SUPPLY) * ASSUMED_PRICE_USD
        ),
        "issued_supply": ISSUED_SUPPLY,
        "circulating_supply": CIRCULATING_SUPPLY,
        "market_price_usd": MARKET_PRICE_USD,
        "token_contract_deployed": TOKEN_CONTRACT_DEPLOYED,
        "transfers_enabled": TRANSFERS_ENABLED,
        "allocations": allocations,
        "vesting": deepcopy(VESTING),
        "circulation_ceilings_are_illustrative_only": True,
        "circulation_ceilings": deepcopy(list(CIRCULATION_CEILINGS)),
        "valuation_disclaimer": (
            "Assumed price and FDV are arithmetic scenarios only; they are not a "
            "market quote, company valuation, forecast, guarantee, or promise."
        ),
    }


def calculate_scenario(price_usd, circulating_units=0):
    """Calculate hypothetical FDV and circulating market cap without asserting value."""
    try:
        price = Decimal(str(price_usd))
        circulating = int(circulating_units)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("price and circulating units must be numeric") from exc
    if not price.is_finite() or price < 0:
        raise ValueError("price must be a finite non-negative number")
    if circulating < 0 or circulating > MAX_SUPPLY:
        raise ValueError("circulating units must be between zero and maximum supply")
    return {
        "assumed_price_usd": str(price),
        "hypothetical_fully_diluted_valuation_usd": str(price * MAX_SUPPLY),
        "hypothetical_circulating_market_cap_usd": str(price * circulating),
        "is_market_quote": False,
    }
