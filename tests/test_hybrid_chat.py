import unittest
from unittest.mock import patch

from xparallel.hybrid_chat import chat


MESSAGES = [{"role": "user", "content": "Hello"}]


class HybridChatTests(unittest.TestCase):
    @patch("xparallel.hybrid_chat.search_memories", return_value=[])
    @patch("xparallel.hybrid_chat._post_json", return_value={"message": {"content": "Local answer"}})
    def test_local_ollama_is_preferred(self, post, memories):
        result = chat(MESSAGES, environ={
            "XP_HUB_LOCAL_URL": "http://localhost:11434",
            "XP_HUB_LOCAL_MODEL": "qwen2.5:3b",
            "XP_HUB_FREE_PROVIDER_URL": "https://api.example.test/v1",
            "XP_HUB_FREE_PROVIDER_MODEL": "free-model",
            "XP_HUB_FREE_PROVIDER_API_KEY": "secret",
            "XP_HUB_FREE_PROVIDER_STATUS": "available",
            "XP_HUB_ALLOW_FREE_FALLBACK": "true",
        })
        self.assertEqual(result["provider"], "local-ollama")
        self.assertFalse(result["fallback_used"])
        self.assertEqual(post.call_count, 1)
        self.assertIn("localhost:11434/api/chat", post.call_args.args[0])

    @patch("xparallel.hybrid_chat.search_memories", return_value=[])
    @patch("xparallel.hybrid_chat._post_json", side_effect=[
        RuntimeError("hybrid_provider_request_failed"),
        {"choices": [{"message": {"content": "Free answer"}}]},
    ])
    def test_free_fallback_requires_explicit_status_and_flag(self, post, memories):
        result = chat(MESSAGES, environ={
            "XP_HUB_LOCAL_URL": "http://localhost:11434",
            "XP_HUB_LOCAL_MODEL": "qwen2.5:3b",
            "XP_HUB_FREE_PROVIDER_URL": "https://api.example.test/v1",
            "XP_HUB_FREE_PROVIDER_MODEL": "free-model",
            "XP_HUB_FREE_PROVIDER_API_KEY": "secret",
            "XP_HUB_FREE_PROVIDER_STATUS": "available",
            "XP_HUB_ALLOW_FREE_FALLBACK": "true",
        })
        self.assertEqual(result["provider"], "free-cloud")
        self.assertTrue(result["fallback_used"])
        self.assertEqual(post.call_count, 2)

    @patch("xparallel.hybrid_chat.search_memories", return_value=[])
    @patch("xparallel.hybrid_chat._post_json", side_effect=RuntimeError("hybrid_provider_request_failed"))
    def test_no_cloud_fallback_without_explicit_opt_in(self, post, memories):
        with self.assertRaisesRegex(RuntimeError, "hybrid_provider_request_failed"):
            chat(MESSAGES, environ={
                "XP_HUB_LOCAL_URL": "http://localhost:11434",
                "XP_HUB_LOCAL_MODEL": "qwen2.5:3b",
                "XP_HUB_FREE_PROVIDER_URL": "https://api.example.test/v1",
                "XP_HUB_FREE_PROVIDER_MODEL": "free-model",
                "XP_HUB_FREE_PROVIDER_API_KEY": "secret",
                "XP_HUB_FREE_PROVIDER_STATUS": "available",
            })
        self.assertEqual(post.call_count, 1)

    @patch("xparallel.hybrid_chat.search_memories", return_value=[])
    def test_no_provider_is_a_clear_unavailable_error(self, memories):
        with self.assertRaisesRegex(RuntimeError, "hybrid_provider_not_configured"):
            chat(MESSAGES, environ={})

    @patch("xparallel.hybrid_chat.search_memories", return_value=[])
    def test_remote_plain_http_is_rejected(self, memories):
        with self.assertRaisesRegex(RuntimeError, "hybrid_provider_url_must_use_https_or_localhost"):
            chat(MESSAGES, environ={
                "XP_HUB_LOCAL_URL": "http://192.168.1.10:11434",
                "XP_HUB_LOCAL_MODEL": "qwen2.5:3b",
            })


if __name__ == "__main__":
    unittest.main()
