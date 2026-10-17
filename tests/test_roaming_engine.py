import json
import os
import unittest
from unittest.mock import patch

from xparallel import roaming_engine


class RoamingEngineTests(unittest.TestCase):
    def test_missing_search_provider_is_explicitly_unavailable(self):
        with patch.dict(os.environ, {}, clear=True):
            result = roaming_engine.roam("find current documentation")
        self.assertEqual(result["status"], "roaming_unavailable")
        self.assertFalse(result["execution_performed"])
        self.assertTrue(any(x["reason"] == "TAVILY_API_KEY_not_configured" for x in result["skipped_providers"]))

    def test_empty_and_oversized_queries_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "query_required"):
            roaming_engine.roam("")
        with self.assertRaisesRegex(ValueError, "query_too_large"):
            roaming_engine.roam("x" * (roaming_engine.MAX_QUERY + 1))

    def test_worker_requires_explicit_host_allowlist(self):
        config = json.dumps([{"name": "worker-a", "url": "https://worker.example", "token": "test-token"}])
        with patch.dict(os.environ, {
            "ONEAI_ROAMING_WORKERS": config,
            "ONEAI_ROAMING_ALLOWED_HOSTS": "",
        }, clear=True):
            workers, skipped = roaming_engine._workers()
        self.assertEqual(workers, [])
        self.assertEqual(skipped[0]["reason"], "worker_host_not_in_ONEAI_ROAMING_ALLOWED_HOSTS")

    def test_non_public_worker_addresses_are_rejected(self):
        config = json.dumps([{"name": "worker-a", "url": "https://worker.example", "token": "test-token"}])
        with patch.dict(os.environ, {
            "ONEAI_ROAMING_WORKERS": config,
            "ONEAI_ROAMING_ALLOWED_HOSTS": "worker.example",
        }, clear=True), patch.object(roaming_engine, "_public_host", return_value=False):
            workers, skipped = roaming_engine._workers()
        self.assertEqual(workers, [])
        self.assertEqual(skipped[0]["reason"], "worker_host_must_resolve_only_to_public_addresses")

    def test_worker_routing_is_search_only_and_reports_no_execution(self):
        config = json.dumps([{"name": "worker-a", "url": "https://worker.example", "token": "test-token"}])
        response = {"operation": "search", "answer": "A sourced result", "sources": [{"title": "Doc", "url": "https://docs.example/page", "snippet": "Text"}]}
        with patch.dict(os.environ, {
            "ONEAI_ROAMING_WORKERS": config,
            "ONEAI_ROAMING_ALLOWED_HOSTS": "worker.example",
        }, clear=True), patch.object(roaming_engine, "_public_host", return_value=True), \
             patch.object(roaming_engine, "_request_json", return_value=response) as request:
            result = roaming_engine.roam("search docs")
        self.assertEqual(result["status"], "success")
        self.assertFalse(result["execution_performed"])
        self.assertEqual(result["sources"][0]["url"], "https://docs.example/page")
        self.assertEqual(request.call_args.args[1]["operation"], "search")


if __name__ == "__main__":
    unittest.main()
