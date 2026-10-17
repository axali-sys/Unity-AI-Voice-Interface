"""Unit tests for the internet-wide OneAI roaming planner."""
import unittest

from xparallel.roaming import plan_roaming


class RoamingPlannerTests(unittest.TestCase):
    def test_roaming_is_internet_wide_not_domain_restricted(self):
        result = plan_roaming("Find a useful online service for my goal")
        self.assertEqual(result["scope"], "internet_wide")
        self.assertFalse(result["domain_restriction"])
        self.assertEqual(result["mode"], "internet_wide_plan_only")
        self.assertIn("goal_driven_dynamic_discovery", result["discovery_strategy"]["approach"])

    def test_plan_does_not_execute_and_flags_consequential_actions(self):
        result = plan_roaming("Deploy the updated application")
        self.assertEqual(result["mode"], "internet_wide_plan_only")
        self.assertFalse(result["execution_performed"])
        self.assertTrue(result["approval_required"])

    def test_planner_does_not_claim_live_internet_access(self):
        result = plan_roaming("Research a topic across the internet")
        self.assertEqual(result["configured_connector_count"], 0)
        self.assertIn("does not browse the live internet", result["notice"])

    def test_empty_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "query_required"):
            plan_roaming("   ")

    def test_oversized_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "query_too_large"):
            plan_roaming("x" * 12001)


if __name__ == "__main__":
    unittest.main()
