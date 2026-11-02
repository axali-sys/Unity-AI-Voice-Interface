import os
import tempfile
import unittest

from xparallel import roaming_registry as registry


class RoamingTaskQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous_db = os.environ.get("XP_ROAMING_DB")
        os.environ["XP_ROAMING_DB"] = os.path.join(self.tmp.name, "roaming.sqlite3")
        self.runtime = registry.register_runtime(
            "worker-test", "Test worker", "https://worker.example",
            ["chat", "build"], ttl_seconds=300,
        )
        self.token = self.runtime["runtime_token"]

    def tearDown(self):
        if self.previous_db is None:
            os.environ.pop("XP_ROAMING_DB", None)
        else:
            os.environ["XP_ROAMING_DB"] = self.previous_db
        self.tmp.cleanup()

    def test_dispatch_claim_and_complete(self):
        queued = registry.enqueue_task(
            "worker-test", "chat", {"prompt": "hello"}, "workspace-a"
        )
        self.assertEqual(queued["status"], "queued")

        claimed = registry.claim_task("worker-test", self.token)
        self.assertEqual(claimed["task_id"], queued["task_id"])
        self.assertEqual(claimed["payload"], {"prompt": "hello"})
        self.assertEqual(claimed["workspace_id"], "workspace-a")
        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["attempts"], 1)
        self.assertIsNone(registry.claim_task("worker-test", self.token))

        completed = registry.complete_task(
            "worker-test", self.token, queued["task_id"], {"answer": "world"}
        )
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["result"], {"answer": "world"})

    def test_runtime_token_is_required_to_claim_and_complete(self):
        registry.enqueue_task("worker-test", "chat", {"prompt": "private"})
        with self.assertRaises(PermissionError):
            registry.claim_task("worker-test", "wrong-token")
        claimed = registry.claim_task("worker-test", self.token)
        with self.assertRaises(PermissionError):
            registry.complete_task(
                "worker-test", "wrong-token", claimed["task_id"], {"ok": True}
            )

    def test_cannot_dispatch_to_offline_or_unknown_runtime(self):
        with self.assertRaises(LookupError):
            registry.enqueue_task("missing-worker", "chat", {"prompt": "x"})

    def test_payload_limits_and_types(self):
        with self.assertRaises(ValueError):
            registry.enqueue_task("worker-test", "chat", ["not", "an", "object"])
        with self.assertRaises(ValueError):
            registry.enqueue_task("worker-test", "chat", {"blob": "x" * 65000})


if __name__ == "__main__":
    unittest.main()
