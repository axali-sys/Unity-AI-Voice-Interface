"""Host-invoked bounded recovery service for pending XParallel execution receipts.

This service never starts or retries workloads. It only asks the approved worker
to finish receipt recovery from immutable, already-persisted finalization data.
A host supervisor must explicitly start and stop the service.
"""
from __future__ import annotations

import threading
from typing import Any, Callable


class ExecutionRecoveryService:
    """Single-flight recovery loop using a fresh authenticated executor session.

    The session provider must return a short-lived bearer token for an executor
    authorized to recover its own jobs. The approval registry independently
    authenticates that token and workspace on every batch.
    """

    def __init__(
        self, *, worker: Any, session_provider: Callable[[], str],
        batch_limit: int = 25, interval_seconds: float = 30.0,
        on_error: Callable[[str], None] | None = None,
    ):
        if not callable(getattr(worker, "recover_pending_finalizations", None)):
            raise TypeError("approved_execution_worker_required")
        if not callable(session_provider):
            raise TypeError("trusted_executor_session_provider_required")
        if not isinstance(batch_limit, int) or isinstance(batch_limit, bool) or not 1 <= batch_limit <= 100:
            raise ValueError("recovery_batch_limit_out_of_range")
        if (not isinstance(interval_seconds, (int, float))
                or isinstance(interval_seconds, bool)
                or not 5 <= interval_seconds <= 3600):
            raise ValueError("recovery_interval_out_of_range")
        if on_error is not None and not callable(on_error):
            raise TypeError("recovery_error_callback_must_be_callable")
        self._worker = worker
        self._session_provider = session_provider
        self._batch_limit = batch_limit
        self._interval = float(interval_seconds)
        self._on_error = on_error
        self._cycle_lock = threading.Lock()

    def run_once(self) -> dict[str, Any]:
        """Run one bounded recovery cycle; overlapping invocations are skipped."""
        if not self._cycle_lock.acquire(blocking=False):
            return {
                "status": "busy", "scanned": 0, "recovered": 0, "pending": 0,
                "results": [],
            }
        try:
            session = self._session_provider()
            if not isinstance(session, str) or not session.strip():
                raise PermissionError("trusted_executor_session_unavailable")
            summary = self._worker.recover_pending_finalizations(
                session, limit=self._batch_limit
            )
            if not isinstance(summary, dict):
                raise TypeError("invalid_execution_recovery_summary")
            for field in ("scanned", "recovered", "pending"):
                value = summary.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    raise ValueError("invalid_execution_recovery_summary")
            if summary["recovered"] + summary["pending"] > summary["scanned"]:
                raise ValueError("inconsistent_execution_recovery_summary")
            return {"status": "ok", **summary}
        finally:
            self._cycle_lock.release()

    def run_forever(self, stop_event: threading.Event) -> None:
        """Run under a host supervisor until stop_event is set.

        Failures are reported by exception class only; the loop remains alive.
        Authentication is retried with a fresh session on the next cycle.
        """
        if not callable(getattr(stop_event, "wait", None)) or not callable(getattr(stop_event, "is_set", None)):
            raise TypeError("threading_stop_event_required")
        while not stop_event.is_set():
            try:
                self.run_once()
            except Exception as exc:
                if self._on_error is not None:
                    try:
                        self._on_error(type(exc).__name__)
                    except Exception:
                        pass
            if stop_event.wait(self._interval):
                break
