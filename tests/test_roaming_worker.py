import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from xparallel.roaming_worker import XParallelWorker, WorkerError


class RoamingWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.token_file = Path(self.tmp.name) / "worker.token"
        self.worker = XParallelWorker(
            "https://xparallel.example", "worker-1", "Test Worker",
            "https://worker.example", token_file=self.token_file,
            owner_token="owner-secret", poll_seconds=1,
            heartbeat_seconds=10,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_registration_saves_runtime_token_and_heartbeat_uses_it(self):
        self.worker._request = Mock(return_value={
            "runtime_id": "worker-1", "runtime_token": "r" * 48
        })
        self.worker.register()
        self.assertEqual(self.worker.runtime_token, "r" * 48)
        self.assertEqual(self.token_file.read_text().strip(), "r" * 48)
        self.assertEqual(self.token_file.stat().st_mode & 0o777, 0o600)
        self.worker._request.assert_called_once()
        args = self.worker._request.call_args.args
        self.assertEqual(args[0], "/roaming/register")
        self.assertEqual(args[2], "owner-secret")

    def test_existing_token_is_reused_and_heartbeat_validates_it(self):
        self.token_file.write_text("saved-runtime-token")
        self.worker._request = Mock(return_value={"status": "online"})
        self.worker.register()
        self.assertEqual(self.worker.runtime_token, "saved-runtime-token")
        self.worker._request.assert_called_once_with(
            "/roaming/heartbeat", {"runtime_id": "worker-1"},
            "saved-runtime-token",
        )

    def test_only_allowlisted_handlers_execute_and_return_hashes(self):
        result = self.worker.execute({
            "task_type": "text.uppercase", "payload": {"text": "hello"}
        })
        self.assertEqual(result["output"], {"text": "HELLO"})
        self.assertTrue(result["verified"])
        self.assertEqual(len(result["input_sha256"]), 64)
        self.assertEqual(len(result["output_sha256"]), 64)
        with self.assertRaises(ValueError):
            self.worker.execute({"task_type": "shell", "payload": {"cmd": "whoami"}})

    def test_uppercase_rejects_non_text_and_oversize_input(self):
        with self.assertRaises(ValueError):
            self.worker.execute({"task_type": "text.uppercase", "payload": {"text": 42}})
        with self.assertRaises(ValueError):
            self.worker.execute({"task_type": "text.uppercase", "payload": {"text": "x" * 16001}})

    def test_run_once_claims_executes_and_completes(self):
        self.worker.runtime_token = "runtime-secret"
        self.worker._request = Mock(side_effect=[
            {"task": {"task_id": "task-1", "task_type": "echo", "payload": {"v": 7}}},
            {"status": "completed"},
        ])
        self.worker._last_heartbeat = __import__("time").monotonic()
        self.assertTrue(self.worker.run_once())
        self.assertEqual(self.worker._request.call_count, 2)
        completion = self.worker._request.call_args.args[1]
        self.assertEqual(completion["task_id"], "task-1")
        self.assertEqual(completion["result"]["output"], {"echo": {"v": 7}})
        self.assertFalse(completion["failed"])

    def test_worker_requires_https_for_remote_control_plane(self):
        with self.assertRaises(ValueError):
            XParallelWorker("http://xparallel.example", "worker-1", "Worker", "https://worker.example")


if __name__ == "__main__":
    unittest.main()
