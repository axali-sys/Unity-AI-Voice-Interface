import threading
import unittest

from xparallel.execution_recovery_service import ExecutionRecoveryService


class FakeWorker:
    def __init__(self):
        self.calls = []
        self.summary = {"scanned": 2, "recovered": 1, "pending": 1, "results": []}

    def recover_pending_finalizations(self, session, *, limit):
        self.calls.append((session, limit))
        return self.summary


class ExecutionRecoveryServiceTests(unittest.TestCase):
    def test_cycle_uses_fresh_executor_session_and_bounded_batch(self):
        worker = FakeWorker()
        sessions = iter(["short-lived-token"])
        service = ExecutionRecoveryService(
            worker=worker, session_provider=lambda: next(sessions),
            batch_limit=7, interval_seconds=10,
        )
        result = service.run_once()
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["recovered"], 1)
        self.assertEqual(worker.calls, [("short-lived-token", 7)])

    def test_missing_session_fails_closed_without_calling_worker(self):
        worker = FakeWorker()
        service = ExecutionRecoveryService(
            worker=worker, session_provider=lambda: "",
        )
        with self.assertRaises(PermissionError):
            service.run_once()
        self.assertEqual(worker.calls, [])

    def test_overlapping_cycle_is_skipped(self):
        worker = FakeWorker()
        entered = threading.Event()
        release = threading.Event()

        def session_provider():
            entered.set()
            self.assertTrue(release.wait(2))
            return "executor-token"

        service = ExecutionRecoveryService(
            worker=worker, session_provider=session_provider,
        )
        first = threading.Thread(target=service.run_once)
        first.start()
        self.assertTrue(entered.wait(2))
        second = service.run_once()
        self.assertEqual(second["status"], "busy")
        release.set()
        first.join(2)
        self.assertFalse(first.is_alive())
        self.assertEqual(len(worker.calls), 1)

    def test_invalid_recovery_summary_is_rejected(self):
        worker = FakeWorker()
        worker.summary = {"scanned": 1, "recovered": 2, "pending": 0}
        service = ExecutionRecoveryService(
            worker=worker, session_provider=lambda: "executor-token",
        )
        with self.assertRaises(ValueError):
            service.run_once()

    def test_batch_and_interval_limits_are_enforced(self):
        worker = FakeWorker()
        with self.assertRaises(ValueError):
            ExecutionRecoveryService(
                worker=worker, session_provider=lambda: "token", batch_limit=101,
            )
        with self.assertRaises(ValueError):
            ExecutionRecoveryService(
                worker=worker, session_provider=lambda: "token", interval_seconds=1,
            )


if __name__ == "__main__":
    unittest.main()
