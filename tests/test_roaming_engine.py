import os
import unittest
from unittest.mock import patch

from xparallel import roaming_engine


class RoamingEngineTests(unittest.TestCase):
    def test_empty_query_rejected(self):
        with self.assertRaisesRegex(ValueError, "query_required"):
            roaming_engine.roam("  ")

    def test_missing_search_provider_is_explicit(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": ""}, clear=False), patch.object(roaming_engine, "_workers", return_value=([], [])):
            result = roaming_engine.roam("find public climate data")
        self.assertEqual(result["status"], "roaming_unavailable")
        self.assertFalse(result["execution_performed"])
        self.assertTrue(any(p["provider"] == "tavily" for p in result["skipped_providers"]))
        self.assertTrue(result["setup"])

    def test_search_returns_grounded_source_metadata(self):
        fake = {"answer": "A concise answer", "results": [{"title": "Example", "url": "https://example.org/page", "content": "Evidence excerpt", "score": 0.9}]}
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test-key"}, clear=False), patch.object(roaming_engine, "_post", return_value=fake), patch.object(roaming_engine, "_workers", return_value=([], [])):
            result = roaming_engine.roam("example query")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["sources"][0]["url"], "https://example.org/page")
        self.assertEqual(result["providers"][0]["provider"], "tavily")
        self.assertTrue(result["execution_performed"])

    def test_action_word_requires_approval(self):
        with patch.dict(os.environ, {"TAVILY_API_KEY": ""}, clear=False), patch.object(roaming_engine, "_workers", return_value=([], [])):
            result = roaming_engine.roam("publish a new public post")
        self.assertTrue(result["approval_required"])

    def test_invalid_worker_config_is_reported(self):
        with patch.dict(os.environ, {"ONEAI_ROAMING_WORKERS": "not-json", "TAVILY_API_KEY": ""}, clear=False):
            result = roaming_engine.roam("check worker configuration")
        self.assertTrue(any(p["provider"] == "remote_workers" for p in result["skipped_providers"]))


if __name__ == "__main__":
    unittest.main()
