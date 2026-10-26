"""End-to-end chat response + conversation persistence checks without live provider calls.

The provider HTTP response is mocked so CI needs no API key or paid AI usage.
Conversation storage is exercised using the existing SQLite implementation.
"""
import json
import os
import tempfile
import unittest
from unittest.mock import patch
from xparallel.chat_service import chat
from xparallel.conversation_store import save_conversation, get_conversation, list_conversations


class ChatConversationFlowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            "XP_MEMORY_DB": os.path.join(self.temp.name, "memory.sqlite3"),
            "XP_AI_API_KEY": "test-only-not-a-real-key",
            "XP_AI_CHAT_COMPLETIONS_URL": "https://provider.example.test/v1/chat/completions",
            "XP_AI_MODEL": "test-model",
        })
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_send_receive_save_retrieve_and_isolate_workspace(self):
        class FakeResponse:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, limit):
                return json.dumps({"choices": [{"message": {"content": "Hello from the mocked provider."}}]}).encode()

        messages = [{"role": "user", "content": "Hello OneAI"}]
        with patch("xparallel.chat_service.urlopen", return_value=FakeResponse()) as request:
            response = chat(messages, workspace_id="workspace-a", use_memory=False)

        self.assertEqual(response["answer"], "Hello from the mocked provider.")
        self.assertEqual(response["model"], "test-model")
        request.assert_called_once()
        request_body = json.loads(request.call_args.args[0].data.decode())
        self.assertEqual(request_body["messages"][-1]["content"], "Hello OneAI")

        save_conversation("conversation-1", "workspace-a", "OneAI test", [
            {"role": "user", "content": "Hello OneAI"},
            {"role": "assistant", "content": response["answer"]},
        ])
        loaded = get_conversation("conversation-1", "workspace-a")
        self.assertEqual(loaded["messages"][1]["content"], response["answer"])
        self.assertIsNone(get_conversation("conversation-1", "workspace-b"))
        self.assertEqual(list_conversations("workspace-b"), [])


if __name__ == "__main__":
    unittest.main()
