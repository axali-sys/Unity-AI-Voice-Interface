import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch

from xparallel.memory_service import summarize_memories


class MemorySummarizationTests(unittest.TestCase):
    def setUp(self):
        self.matches = [{
            "id": "mem-1",
            "summary": "Deployment preference",
            "content": "Preserve existing routes and require human approval.",
            "tags": ["decision"],
            "score": 2,
        }]

    @patch("xparallel.memory_service.search_memories", return_value=[])
    def test_no_matches_does_not_call_provider(self, _search):
        with patch.dict(os.environ, {}, clear=True):
            result = summarize_memories("deployment", "workspace-a")
        self.assertEqual(result["summary"], "")
        self.assertEqual(result["memories"], [])
        self.assertEqual(result["provider"], "none")

    @patch("xparallel.memory_service.search_memories")
    def test_missing_provider_key_fails_explicitly(self, search):
        search.return_value = self.matches
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "ai_provider_not_configured"):
                summarize_memories("deployment", "workspace-a")

    @patch("xparallel.memory_service.urlopen")
    @patch("xparallel.memory_service.search_memories")
    def test_provider_summary_is_returned_with_source_ids(self, search, open_url):
        search.return_value = self.matches
        payload = {"choices": [{"message": {"content": "Keep routes and approval gates intact. [mem-1]"}}]}
        open_url.return_value.__enter__.return_value = BytesIO(json.dumps(payload).encode())
        with patch.dict(os.environ, {"XP_AI_API_KEY": "test-only", "XP_AI_MODEL": "test-model"}):
            result = summarize_memories("deployment", "workspace-a")
        self.assertIn("[mem-1]", result["summary"])
        self.assertEqual(result["provider"], "test-model")
        self.assertEqual(result["memories"][0]["id"], "mem-1")
        request = open_url.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer test-only")

    @patch("xparallel.memory_service.urlopen")
    @patch("xparallel.memory_service.search_memories")
    def test_invalid_provider_response_is_rejected(self, search, open_url):
        search.return_value = self.matches
        open_url.return_value.__enter__.return_value = BytesIO(b'{"choices":[]}')
        with patch.dict(os.environ, {"XP_AI_API_KEY": "test-only"}):
            with self.assertRaisesRegex(RuntimeError, "ai_provider_invalid_response"):
                summarize_memories("deployment", "workspace-a")


if __name__ == "__main__":
    unittest.main()
