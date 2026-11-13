"""Explicit host lifecycle for the XParallel receipt-recovery service.

Nothing starts at import time. A deployment host must construct this supervisor,
supply a trusted executor-session provider, and call start() deliberately.
"""
from __future__ import annotations

import threading
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
        build_worker = getattr(host_services, "build_worker", None)
        if not callable(build_worker):
            raise TypeError("trusted_execution_host_services_required")
        self._service = ExecutionRecoveryService(
            worker=build_worker(), session_provider=session_provider,
            batch_limit=batch_limit, interval_seconds=interval_seconds,
            on_error=on_error,
        )
        self._enabled = enabled
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()
        self._last_error: str | None = None

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
        try:
            self._service.run_forever(self._stop)
        except Exception as exc:
            # The thread boundary must not leak adapter details or credentials.
            with self._lock:
                self._last_error = type(exc).__name__

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
        with self._lock:
            running = self._thread is not None and self._thread.is_alive()
            return {
                "enabled": self._enabled,
                "running": running,
                "last_error_type": self._last_error,
            }
