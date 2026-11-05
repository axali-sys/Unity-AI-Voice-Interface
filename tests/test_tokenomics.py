import unittest
from decimal import Decimal

from xparallel.tokenomics import (
    CIRCULATION_CEILINGS,
    MAX_SUPPLY,
    calculate_scenario,
    get_tokenomics_proposal,
)


class TokenomicsProposalTests(unittest.TestCase):
    def test_allocations_equal_maximum_supply(self):
        proposal = get_tokenomics_proposal()
        self.assertEqual(sum(item["units"] for item in proposal["allocations"]), MAX_SUPPLY)
        self.assertEqual(sum(item["basis_points"] for item in proposal["allocations"]), 10_000)

    def test_founder_allocation_is_requested_half(self):
        proposal = get_tokenomics_proposal()
        founders = next(item for item in proposal["allocations"] if item["key"] == "founders")
        self.assertEqual(founders["units"], 500_000_000)
        self.assertEqual(founders["basis_points"], 5_000)

    def test_proposal_does_not_claim_issuance_or_market_price(self):
        proposal = get_tokenomics_proposal()
        self.assertEqual(proposal["status"], "proposal_only")
        self.assertEqual(proposal["issued_supply"], 0)
        self.assertEqual(proposal["circulating_supply"], 0)
        self.assertIsNone(proposal["market_price_usd"])
        self.assertFalse(proposal["token_contract_deployed"])
        self.assertFalse(proposal["transfers_enabled"])

    def test_assumed_one_dollar_fdv_is_arithmetic_only(self):
        result = calculate_scenario("1.00", 100_000_000)
        self.assertEqual(Decimal(result["hypothetical_fully_diluted_valuation_usd"]), Decimal("1000000000.00"))
        self.assertEqual(Decimal(result["hypothetical_circulating_market_cap_usd"]), Decimal("100000000.00"))
        self.assertFalse(result["is_market_quote"])

    def test_rejects_circulation_above_cap(self):
        with self.assertRaises(ValueError):
            calculate_scenario("1", MAX_SUPPLY + 1)

    def test_rejects_negative_or_invalid_price(self):
        for price in ("-1", "NaN", "not-a-price"):
            with self.subTest(price=price):
                with self.assertRaises(ValueError):
                    calculate_scenario(price, 0)

    def test_circulation_ceilings_are_monotonic_and_below_cap(self):
        units = [row["units"] for row in CIRCULATION_CEILINGS]
        self.assertEqual(units, sorted(units))
        self.assertTrue(all(0 <= value <= MAX_SUPPLY for value in units))

    def test_proposal_returns_defensive_copy(self):
        proposal = get_tokenomics_proposal()
        proposal["allocations"][0]["units"] = 0
        self.assertEqual(
            next(item for item in get_tokenomics_proposal()["allocations"] if item["key"] == "founders")["units"],
            500_000_000,
        )


if __name__ == "__main__":
    unittest.main()
