import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xparallel import plugins


class PluginAdapterTests(unittest.TestCase):
    def test_catalog_does_not_claim_missing_credentials_or_sources(self):
        with patch.dict(os.environ, {}, clear=True):
            result = plugins.plugin_catalog(sandbox_available=False)
        by_id = {p["id"]: p for p in result["plugins"]}
        self.assertEqual(by_id["github"]["status"], "credentials_missing")
        self.assertEqual(by_id["web_search"]["status"], "credentials_missing")
        self.assertEqual(by_id["google_drive"]["status"], "credentials_missing")
        self.assertEqual(by_id["file_retrieval"]["status"], "configuration_required")
        self.assertEqual(by_id["ai_memory"]["status"], "configuration_required")
        self.assertEqual(by_id["xparallel_sandbox"]["status"], "sandbox_unavailable")
        self.assertFalse(any(p["can_execute"] for p in result["plugins"]))

    def test_github_search_calls_real_adapter_with_bearer_token(self):
        response = {"items":[{"full_name":"owner/repo","private":False,"html_url":"https://github.com/owner/repo"}]}
        with patch.dict(os.environ, {"GITHUB_TOKEN":"test-token"}, clear=True), patch.object(plugins,"_http_json",return_value=response) as http:
            result=plugins.execute_plugin("github","search_repositories",{"query":"owner/repo"})
        self.assertEqual(result["state"],"ok")
        self.assertEqual(result["data"]["items"][0]["full_name"],"owner/repo")
        self.assertEqual(http.call_args.args[1]["Authorization"],"Bearer test-token")

    def test_web_search_missing_key_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            result=plugins.execute_plugin("web_search","search",{"query":"test"})
        self.assertEqual(result["state"],"plugin_error")
        self.assertIn("credentials_missing",result["error"])

    def test_file_retrieval_reads_only_within_configured_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); (root/"notes.txt").write_text("XParallel memory note",encoding="utf-8")
            with patch.dict(os.environ,{"XP_FILE_RETRIEVAL_ROOT":tmp},clear=True):
                result=plugins.execute_plugin("file_retrieval","read_file",{"path":"notes.txt"})
                blocked=plugins.execute_plugin("file_retrieval","read_file",{"path":"../outside.txt"})
        self.assertEqual(result["state"],"ok")
        self.assertIn("XParallel",result["text"])
        self.assertEqual(blocked["state"],"plugin_error")
        self.assertIn("path_outside_allowed_root",blocked["error"])

    def test_ai_memory_search_returns_matching_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory=Path(tmp)/"memory.jsonl"
            memory.write_text(json.dumps({"text":"XParallel sandbox approval protocol"})+"\\n"+json.dumps({"text":"unrelated music note"})+"\\n",encoding="utf-8")
            with patch.dict(os.environ,{"XP_AI_MEMORY_PATH":str(memory)},clear=True):
                result=plugins.execute_plugin("ai_memory","search",{"query":"XParallel approval"})
        self.assertEqual(result["state"],"ok")
        self.assertTrue(result["results"])
        self.assertIn("approval",result["results"][0]["text"])

    def test_private_connectors_are_blocked_from_public_mixer(self):
        with patch.dict(os.environ,{"GITHUB_TOKEN":"configured"},clear=True):
            result=plugins.retrieve_plugin_context("repo",["github"],allow_private=False)
        self.assertEqual(result["results"][0]["state"],"blocked")

    def test_sandbox_requires_human_approval(self):
        result=plugins.execute_plugin("xparallel_sandbox","run_tests",{"files":{}},human_approved=False)
        self.assertEqual(result["state"],"approval_required")

    def test_unknown_plugin_is_rejected(self):
        self.assertEqual(plugins.execute_plugin("not-real","run",{})["state"],"plugin_not_found")


if __name__ == "__main__":
    unittest.main()
