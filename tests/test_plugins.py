import os
import unittest
from unittest.mock import patch

from xparallel import plugins


class PluginCatalogTests(unittest.TestCase):
    def test_catalog_marks_unimplemented_adapters_unavailable(self):
        with patch.dict(os.environ, {}, clear=True):
            result = plugins.plugin_catalog(sandbox_available=False)
        by_id = {item["id"]: item for item in result["plugins"]}
        self.assertEqual(by_id["github"]["status"], "credentials_missing")
        self.assertFalse(by_id["github"]["can_execute"])
        self.assertEqual(by_id["google_drive"]["status"], "credentials_missing")
        self.assertEqual(by_id["web_search"]["status"], "credentials_missing")
        self.assertEqual(by_id["file_retrieval"]["status"], "adapter_not_implemented")
        self.assertFalse(by_id["xparallel_sandbox"]["can_execute"])

    def test_plugin_execution_fails_closed_for_known_plugin(self):
        result = plugins.execute_plugin("github", "list_repositories", {})
        self.assertEqual(result["state"], "plugin_unavailable")
        self.assertEqual(result["reason"], "adapter_not_implemented")

    def test_unknown_plugin_is_rejected(self):
        result = plugins.execute_plugin("random", "run", {})
        self.assertEqual(result["state"], "plugin_not_found")

    def test_catalog_does_not_grant_execution_permission(self):
        with patch.dict(os.environ, {"GITHUB_TOKEN": "configured"}, clear=True):
            result = plugins.plugin_catalog()
        github = next(p for p in result["plugins"] if p["id"] == "github")
        self.assertEqual(github["status"], "adapter_not_implemented")
        self.assertFalse(github["can_execute"])


if __name__ == "__main__":
    unittest.main()
