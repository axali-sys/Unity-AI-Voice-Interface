import os
import unittest

from xparallel.organization import Member, normalize_org, can
from xparallel.billing_profile import billing_profile, invoice_request


class OrganizationBillingTests(unittest.TestCase):
    def test_org_membership(self):
        member = Member("a", "Acme Inc", "owner")
        self.assertEqual(normalize_org("Acme Inc"), "acme-inc")
        self.assertTrue(can(member, "admin"))
        self.assertFalse(can(Member("v", "acme", "viewer"), "operator"))

    def test_billing_is_preview_only(self):
        previous = os.environ.get("XP_BILLING_EMAIL")
        try:
            os.environ["XP_BILLING_EMAIL"] = "billing@example.com"
            profile = billing_profile("Acme Inc")
            self.assertEqual(profile["email"], "billing@example.com")
            self.assertEqual(profile["payment_status"], "not_connected")
            self.assertEqual(profile["organization_id"], "acme inc")
            invoice = invoice_request(
                "ACME INC",
                [{"workspace_id": "acme inc", "units": 5}],
            )
            self.assertEqual(invoice["amount"], 5)
        finally:
            if previous is None:
                os.environ.pop("XP_BILLING_EMAIL", None)
            else:
                os.environ["XP_BILLING_EMAIL"] = previous


if __name__ == "__main__":
    unittest.main()
