import unittest
from xparallel.provider_catalog import configured_providers


class ProviderCatalogTests(unittest.TestCase):
    def test_empty_environment_has_no_providers(self):
        self.assertEqual(configured_providers({}), [])

    def test_local_requires_url_and_model_and_stays_unknown(self):
        self.assertEqual(configured_providers({"XP_HUB_LOCAL_URL": "http://localhost:11434"}), [])
        providers = configured_providers({
            "XP_HUB_LOCAL_URL": "http://localhost:11434",
            "XP_HUB_LOCAL_MODEL": "qwen2.5:3b",
        })
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0].kind, "local")
        self.assertEqual(providers[0].status, "unknown")

    def test_free_cloud_requires_id_model_and_key(self):
        incomplete = configured_providers({
            "XP_HUB_FREE_PROVIDER_ID": "provider",
            "XP_HUB_FREE_PROVIDER_MODEL": "model",
        })
        self.assertEqual(incomplete, [])
        providers = configured_providers({
            "XP_HUB_FREE_PROVIDER_ID": "provider",
            "XP_HUB_FREE_PROVIDER_MODEL": "model",
            "XP_HUB_FREE_PROVIDER_API_KEY": "never-return-this",
        })
        self.assertEqual(len(providers), 1)
        self.assertNotIn("never-return-this", str([p.public_record() for p in providers]))
        self.assertEqual(providers[0].status, "unknown")

    def test_paid_requires_explicit_cost_estimate(self):
        base = {
            "XP_HUB_PAID_PROVIDER_ID": "paid",
            "XP_HUB_PAID_PROVIDER_MODEL": "model",
            "XP_HUB_PAID_PROVIDER_API_KEY": "secret",
        }
        self.assertEqual(configured_providers(base), [])
        providers = configured_providers({**base, "XP_HUB_PAID_ESTIMATED_COST_USD": "0.02"})
        self.assertEqual(len(providers), 1)
        self.assertTrue(providers[0].requires_approval)
        self.assertEqual(providers[0].estimated_cost_usd, 0.02)


if __name__ == "__main__":
    unittest.main()
