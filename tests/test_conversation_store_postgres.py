"""Integration tests for opt-in PostgreSQL conversation history."""
import os, unittest, uuid
from xparallel import conversation_store_postgres as store

@unittest.skipUnless(os.getenv("XP_VERSE_DATABASE_URL"), "requires disposable PostgreSQL database")
class PostgreSQLConversationStoreTests(unittest.TestCase):
    def setUp(self):
        self.workspace="conversation_test_"+uuid.uuid4().hex
        self.conversation="conv_"+uuid.uuid4().hex

    def test_save_retrieve_update_list_delete_and_workspace_isolation(self):
        messages=[{"role":"user","content":"Hello"},{"role":"assistant","content":"Hello from test"}]
        saved=store.save_conversation(self.conversation,self.workspace,"Test conversation",messages)
        self.assertEqual(saved["message_count"],2)
        loaded=store.get_conversation(self.conversation,self.workspace)
        self.assertEqual(loaded["messages"],messages)
        self.assertIsNone(store.get_conversation(self.conversation,self.workspace+"_other"))
        self.assertEqual(store.list_conversations(self.workspace+"_other"),[])
        self.assertEqual(store.list_conversations(self.workspace)[0]["message_count"],2)
        store.save_conversation(self.conversation,self.workspace,"Updated",messages+[{"role":"user","content":"Again"}])
        updated=store.get_conversation(self.conversation,self.workspace)
        self.assertEqual(updated["title"],"Updated")
        self.assertEqual(len(updated["messages"]),3)
        self.assertFalse(store.delete_conversation(self.conversation,self.workspace+"_other"))
        self.assertTrue(store.delete_conversation(self.conversation,self.workspace))
        self.assertIsNone(store.get_conversation(self.conversation,self.workspace))

if __name__ == "__main__":
    unittest.main()
