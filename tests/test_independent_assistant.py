"""Tests for the independent local-first OneAI model path; no network or API key required."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from xparallel.chat_service import chat


class IndependentAssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "XP_MEMORY_DB": os.path.join(self.temp.name, "memory.sqlite3"),
            "XP_OLLAMA_URL": "http://127.0.0.1:11434/api/chat",
            "XP_OLLAMA_MODEL": "qwen2.5:3b",
        }, clear=False)
        self.env.start()
        os.environ.pop("XP_AI_API_KEY", None)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_uses_ollama_without_api_key(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return json.dumps({"message": {"content": "Hello from local OneAI."}}).encode()

        with patch("xparallel.chat_service.urlopen", return_value=FakeResponse()) as request:
            result = chat([{"role": "user", "content": "Hello"}], use_memory=False)
        self.assertEqual(result["answer"], "Hello from local OneAI.")
        self.assertEqual(result["provider"], "ollama")
        self.assertEqual(result["model"], "qwen2.5:3b")
        body = json.loads(request.call_args.args[0].data.decode())
        self.assertFalse(body["stream"])
        self.assertEqual(body["messages"][-1]["content"], "Hello")

    def test_remote_ollama_requires_https(self):
        os.environ["XP_OLLAMA_URL"] = "http://model.example.com/api/chat"
        with self.assertRaisesRegex(RuntimeError, "ollama_remote_url_must_use_https"):
            chat([{"role": "user", "content": "Hello"}], use_memory=False)

    def test_provider_failure_is_not_faked(self):
        from urllib.error import URLError
        with patch("xparallel.chat_service.urlopen", side_effect=URLError("offline")):
            with self.assertRaisesRegex(RuntimeError, "ai_model_unavailable"):
                chat([{"role": "user", "content": "Hello"}], use_memory=False)


if __name__ == "__main__":
    unittest.main()
