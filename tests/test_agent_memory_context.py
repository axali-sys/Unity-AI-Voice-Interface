import unittest

from xparallel.agent import plan


class AgentMemoryContextTests(unittest.TestCase):
    def test_plan_includes_retrieved_memory_context(self):
        context = [{
            "id": "memory-1",
            "summary": "Backup design",
            "content": "XParallel uses workspace-scoped memory.",
            "tags": ["xparallel", "memory"],
            "score": 2,
        }]
        result = plan("build a memory backup plan", context)
        self.assertEqual(result["memory_context"][0]["id"], "memory-1")
        self.assertIn("workspace-scoped", result["memory_context"][0]["content"])

    def test_plan_without_memory_context_remains_compatible(self):
        result = plan("search existing knowledge")
        self.assertEqual(result["memory_context"], [])


if __name__ == "__main__":
    unittest.main()
