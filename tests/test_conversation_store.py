import os
import tempfile
import unittest
from unittest.mock import patch

from xparallel.conversation_store import delete_conversation, get_conversation, list_conversations, save_conversation


class ConversationStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {"XP_MEMORY_DB": os.path.join(self.temp.name, "memory.sqlite3")})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def test_round_trip_persists_messages_and_title(self):
        result = save_conversation("c1", "workspace-a", "Deployment plan", [
            {"role": "user", "content": "Keep existing routes"},
            {"role": "assistant", "content": "I will preserve them."},
        ])
        self.assertEqual(result["message_count"], 2)
        loaded = get_conversation("c1", "workspace-a")
        self.assertEqual(loaded["title"], "Deployment plan")
        self.assertEqual(loaded["messages"][0]["content"], "Keep existing routes")
        self.assertEqual(len(list_conversations("workspace-a")), 1)

    def test_workspace_isolation_and_delete(self):
        save_conversation("same-id", "workspace-a", "A", [{"role": "user", "content": "A data"}])
        self.assertIsNone(get_conversation("same-id", "workspace-b"))
        self.assertEqual(list_conversations("workspace-b"), [])
        self.assertFalse(delete_conversation("same-id", "workspace-b"))
        self.assertTrue(delete_conversation("same-id", "workspace-a"))

    def test_invalid_message_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_message"):
            save_conversation("c1", "workspace-a", "A", [{"role": "system", "content": "not allowed"}])

    def test_message_and_total_size_limits(self):
        with self.assertRaisesRegex(ValueError, "invalid_message_content"):
            save_conversation("c1", "workspace-a", "A", [{"role": "user", "content": "  "}])
        with self.assertRaisesRegex(ValueError, "conversation_too_large"):
            save_conversation("c1", "workspace-a", "A", [{"role": "user", "content": "x" * 24000}] * 21)


if __name__ == "__main__":
    unittest.main()
