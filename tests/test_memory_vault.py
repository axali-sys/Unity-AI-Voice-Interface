import tempfile
import unittest
from pathlib import Path

from xparallel.memory_vault import (
    forget_memory,
    list_memories,
    save_memory,
    search_memories,
)


class MemoryVaultTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp_dir.name) / "memory.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_deduplicates_identical_content_in_workspace(self):
        first = save_memory("XParallel stores recoverable memory.", "alpha", db_path=self.db)
        second = save_memory("XParallel stores recoverable memory.", "alpha", db_path=self.db)
        self.assertTrue(first["created"])
        self.assertFalse(second["created"])
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(len(list_memories("alpha", db_path=self.db)), 1)

    def test_workspaces_are_isolated(self):
        save_memory("private project detail", "alpha", db_path=self.db)
        self.assertEqual(list_memories("beta", db_path=self.db), [])

    def test_search_returns_relevant_source(self):
        save_memory("XParallel intelligent backup vault", "alpha", db_path=self.db)
        results = search_memories("backup vault", "alpha", db_path=self.db)
        self.assertEqual(len(results), 1)
        self.assertIn("backup", results[0]["content"])

    def test_forget_removes_record(self):
        item = save_memory("forget me", "alpha", db_path=self.db)
        self.assertTrue(forget_memory(item["id"], "alpha", db_path=self.db))
        self.assertEqual(list_memories("alpha", db_path=self.db), [])

    def test_rejects_empty_or_oversized_content(self):
        with self.assertRaises(ValueError):
            save_memory("  ", db_path=self.db)
        with self.assertRaises(ValueError):
            save_memory("x" * 2_000_001, db_path=self.db)


if __name__ == "__main__":
    unittest.main()
