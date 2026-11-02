import unittest
from xparallel.free_access_hub import Provider, select_provider

class FreeAccessHubTests(unittest.TestCase):
    def setUp(self):
        self.local = Provider("ollama-local", "local", ("chat", "summarize"),
                              "available", configured=True)
        self.free = Provider("free-cloud", "free_cloud", ("chat", "summarize"),
                             "available", configured=True)
        self.paid = Provider("paid-api", "paid", ("chat",), "available",
                             0.01, True, True)

    def test_hybrid_prefers_local_provider(self):
        d = select_provider("chat", [self.free, self.local])
        self.assertEqual(d.status, "selected")
        self.assertEqual(d.provider_id, "ollama-local")
        self.assertEqual(d.estimated_cost_usd, 0.0)

    def test_free_cloud_fallback_when_local_unavailable(self):
        local = Provider("ollama-local", "local", ("chat",), "unavailable",
                         configured=True)
        self.assertEqual(select_provider("chat", [local, self.free]).provider_id,
                         "free-cloud")

    def test_paid_never_selected_without_explicit_approval(self):
        d = select_provider("chat", [self.paid])
        self.assertEqual(d.status, "needs_configuration")
        self.assertIsNone(d.provider_id)
        self.assertTrue(d.requires_approval)

    def test_paid_requires_both_flags(self):
        self.assertIsNone(select_provider("chat", [self.paid],
            allow_paid=True).provider_id)
        d = select_provider("chat", [self.paid], allow_paid=True,
                            paid_approval_granted=True)
        self.assertEqual(d.provider_id, "paid-api")

    def test_unknown_availability_is_not_available(self):
        unknown = Provider("unknown", "free_cloud", ("chat",), "unknown",
                           configured=True)
        d = select_provider("chat", [unknown])
        self.assertEqual(d.status, "needs_configuration")
        self.assertIsNone(d.provider_id)

    def test_empty_task_rejected(self):
        self.assertEqual(select_provider(" ", [self.local]).status,
                         "no_eligible_provider")

    def test_no_match_does_not_make_paid_call(self):
        d = select_provider("image", [self.local])
        self.assertEqual(d.status, "no_eligible_provider")
        self.assertIn("No paid request was made", d.reason)

if __name__ == "__main__":
    unittest.main()
