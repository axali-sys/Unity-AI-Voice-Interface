import threading
import time
import unittest

from xparallel.execution_recovery_supervisor import ExecutionRecoverySupervisor


class FakeWorker:
    def __init__(self):
        self.calls = 0
        self.called = threading.Event()

    def recover_pending_finalizations(self, session, *, limit):
        self.calls += 1
        self.called.set()
        return {"scanned": 0, "recovered": 0, "pending": 0, "results": []}


class FakeHostServices:
    def __init__(self):
        self.worker = FakeWorker()

    def build_worker(self):
        return self.worker


class ExecutionRecoverySupervisorTests(unittest.TestCase):
    def test_import_style_construction_does_not_start_worker(self):
        host = FakeHostServices()
        supervisor = ExecutionRecoverySupervisor(
            host_services=host, session_provider=lambda: "executor-token",
            enabled=False,
        )
        self.assertEqual(host.worker.calls, 0)
        self.assertEqual(supervisor.start()["reason"], "recovery_not_enabled")
        self.assertFalse(supervisor.health()["running"])
        self.assertEqual(host.worker.calls, 0)

    def test_explicit_start_runs_and_stop_joins_thread(self):
        host = FakeHostServices()
        supervisor = ExecutionRecoverySupervisor(
            host_services=host, session_provider=lambda: "executor-token",
            enabled=True, interval_seconds=5,
        )
        started = supervisor.start()
        self.assertTrue(started["running"])
        self.assertTrue(host.worker.called.wait(2))
        stopped = supervisor.stop(timeout_seconds=2)
        self.assertTrue(stopped["stopped"])
        self.assertFalse(supervisor.health()["running"])
        self.assertGreaterEqual(host.worker.calls, 1)

    def test_start_is_idempotent_and_disabled_by_default(self):
        host = FakeHostServices()
        supervisor = ExecutionRecoverySupervisor(
            host_services=host, session_provider=lambda: "executor-token",
        )
        self.assertFalse(supervisor.health()["enabled"])
        self.assertEqual(supervisor.start()["running"], False)
        self.assertEqual(host.worker.calls, 0)

    def test_invalid_stop_timeout_is_rejected(self):
        supervisor = ExecutionRecoverySupervisor(
            host_services=FakeHostServices(),
            session_provider=lambda: "executor-token", enabled=True,
        )
        with self.assertRaises(ValueError):
            supervisor.stop(timeout_seconds=100)


if __name__ == "__main__":
    unittest.main()
