"""Explicit host lifecycle and health reporting for receipt recovery."""
from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Callable

from xparallel.execution_recovery_service import ExecutionRecoveryService


class ExecutionRecoverySupervisor:
    def __init__(
        self, *, host_services: Any, session_provider: Callable[[], str],
        enabled: bool = False, batch_limit: int = 25,
        interval_seconds: float = 30.0,
        on_error: Callable[[str], None] | None = None,
    ):
        if enabled is not True and enabled is not False:
            raise ValueError("recovery_enable_flag_must_be_boolean")
        if on_error is not None and not callable(on_error):
            raise TypeError("recovery_error_callback_must_be_callable")
        build_worker = getattr(host_services, "build_worker", None)
        if not callable(build_worker):
            raise TypeError("trusted_execution_host_services_required")
        self._enabled = enabled
        self._on_error = on_error
        self._service = ExecutionRecoveryService(
            worker=build_worker(), session_provider=session_provider,
            batch_limit=batch_limit, interval_seconds=interval_seconds,
        )
        self._interval = float(interval_seconds)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_error: str | None = None
        self._last_cycle_at: str | None = None
        self._last_success_at: str | None = None
        self._last_result: dict[str, int] | None = None
        self._consecutive_failures = 0
        self._total_failures = 0
        self._total_recovered = 0

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _record_error(self, exc: Exception) -> None:
        error_type = type(exc).__name__
        with self._lock:
            self._last_cycle_at = self._timestamp()
            self._last_error = error_type
            self._consecutive_failures += 1
            self._total_failures += 1
        # Callback receives only a fixed exception class, never message or token.
        if self._on_error is not None:
            try:
                self._on_error(error_type)
            except Exception:
                pass

    def _record_success(self, result: dict[str, Any]) -> None:
        with self._lock:
            self._last_cycle_at = self._timestamp()
            self._last_success_at = self._last_cycle_at
            self._last_error = None
            self._consecutive_failures = 0
            self._last_result = {
                "scanned": result["scanned"],
                "recovered": result["recovered"],
                "pending": result["pending"],
            }
            self._total_recovered += result["recovered"]

    def start(self) -> dict[str, Any]:
        """Start only when explicitly enabled; repeated start is idempotent."""
        with self._lock:
            if not self._enabled:
                return {"enabled": False, "running": False, "reason": "recovery_not_enabled"}
            if self._thread is not None and self._thread.is_alive():
                return {"enabled": True, "running": True}
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._run, name="xparallel-execution-recovery", daemon=True
            )
            self._thread.start()
            return {"enabled": True, "running": True}

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self._record_success(self._service.run_once())
            except Exception as exc:
                self._record_error(exc)
            if self._stop.wait(self._interval):
                break

    def stop(self, timeout_seconds: float = 5.0) -> dict[str, Any]:
        if (not isinstance(timeout_seconds, (int, float))
                or isinstance(timeout_seconds, bool)
                or not 0 <= timeout_seconds <= 60):
            raise ValueError("recovery_stop_timeout_out_of_range")
        with self._lock:
            thread = self._thread
            if thread is None:
                return {"running": False, "stopped": True}
            self._stop.set()
        thread.join(float(timeout_seconds))
        running = thread.is_alive()
        with self._lock:
            if not running:
                self._thread = None
        return {"running": running, "stopped": not running}

    def health(self) -> dict[str, Any]:
        """Return operational counters only; never expose sessions or adapter data."""
        with self._lock:
            running = self._thread is not None and self._thread.is_alive()
            return {
                "enabled": self._enabled,
                "running": running,
                "last_cycle_at": self._last_cycle_at,
                "last_success_at": self._last_success_at,
                "last_error_type": self._last_error,
                "consecutive_failures": self._consecutive_failures,
                "total_failures": self._total_failures,
                "total_recovered": self._total_recovered,
                "last_result": dict(self._last_result) if self._last_result else None,
            }
