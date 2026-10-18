import unittest
from unittest.mock import AsyncMock, patch

from xparallel import chat_service


class ChatServiceMixerIntegrationTests(unittest.TestCase):
    def test_chat_uses_mixer_and_returns_evidence_and_memory_sources(self):
        with patch.object(chat_service, "search_memories", return_value=[
            {"id": "memory-1", "summary": "project context", "content": "stored source"}
        ]), patch.object(chat_service, "mix", new=AsyncMock(return_value={
            "state": "ok", "final_answer": "Synthesized answer",
            "calls": [{"provider": "openai", "model_id": "configured-model", "status": "success"}],
            "synthesizer": {"provider": "openai", "model_id": "configured-model"},
            "skipped": [],
        })) as mocked_mix:
            result = chat_service.chat([
                {"role": "user", "content": "What is my project?"}
            ], workspace_id="workspace-a")
        self.assertEqual(result["answer"], "Synthesized answer")
        self.assertEqual(result["model"], "configured-model")
        self.assertEqual(result["mixer"]["state"], "ok")
        self.assertEqual(result["memory_sources"][0]["id"], "memory-1")
        args = mocked_mix.await_args.args
        self.assertIn("User: What is my project?", args[0])
        self.assertIn("stored source", args[1])

    def test_chat_rejects_invalid_message_role(self):
        with self.assertRaisesRegex(ValueError, "invalid_message"):
            chat_service.chat([{"role": "system", "content": "not allowed"}])

    def test_chat_requires_final_user_message(self):
        with self.assertRaisesRegex(ValueError, "last_message_must_be_user"):
            chat_service.chat([
                {"role": "user", "content": "question"},
                {"role": "assistant", "content": "answer"},
            ])


if __name__ == "__main__":
    unittest.main()
