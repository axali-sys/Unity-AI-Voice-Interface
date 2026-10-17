"""Unit tests for the OneAI roaming planner."""
import unittest

from xparallel.roaming import plan_roaming


class RoamingPlannerTests(unittest.TestCase):
    def test_selects_multiple_service_categories(self):
        result = plan_roaming("Research CRM customers and draft an email report")
        ids = {service["id"] for service in result["services"]}
        self.assertIn("web_research", ids)
        self.assertIn("business_operations", ids)
        self.assertIn("communication", ids)
        self.assertIn("files_and_knowledge", ids)

    def test_plan_does_not_execute(self):
        result = plan_roaming("deploy the updated application")
        self.assertEqual(result["mode"], "plan_only")
        self.assertFalse(result["execution_performed"])
        self.assertTrue(result["approval_required"])

    def test_empty_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "query_required"):
            plan_roaming("   ")

    def test_oversized_query_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "query_too_large"):
            plan_roaming("x" * 12001)

    def test_unknown_goal_gets_general_assistance_plan(self):
        result = plan_roaming("help me think through a difficult decision")
        self.assertEqual(result["services"][0]["id"], "general_assistance")
        self.assertEqual(result["configured_connector_count"], 0)


if __name__ == "__main__":
    unittest.main()
