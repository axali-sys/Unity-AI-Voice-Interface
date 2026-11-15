"""Host-adapter boundary for XParallel worker leases.

This module defines lease policy only. It deliberately owns no database schema:
the host must provide atomic, durable repository operations before deployment.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable
import uuid


class WorkerLeaseService:
    """Validate worker ownership, expiry, and agent revocation around atomic storage.

    Repository contract:
      claim(workspace_id, task_id, agent_id, worker_id, lease_id, expires_at)
      get(workspace_id, task_id)
      renew(workspace_id, task_id, lease_id, worker_id, expected_version, expires_at)
      release(workspace_id, task_id, lease_id, worker_id, expected_version)

    Mutating repository methods must be atomic and reject stale versions/owners.
    """

    def __init__(
        self, *, repository: Any,
        agent_is_active: Callable[[str, str], bool],
        clock: Callable[[], datetime] | None = None,
        min_ttl_seconds: int = 15,
        max_ttl_seconds: int = 3600,
    ):
        required = ("claim", "get", "renew", "release")
        if any(not callable(getattr(repository, name, None)) for name in required):
            raise TypeError("atomic_worker_lease_repository_required")
        if not callable(agent_is_active):
            raise TypeError("trusted_agent_status_adapter_required")
        if not (1 <= min_ttl_seconds <= max_ttl_seconds <= 86400):
            raise ValueError("invalid_worker_lease_ttl_bounds")
        self._repo = repository
        self._agent_is_active = agent_is_active
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._min_ttl = min_ttl_seconds
        self._max_ttl = max_ttl_seconds

    def current_time(self) -> datetime:
        """Return the service clock as an aware UTC datetime for trusted adapters."""
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError("lease_clock_must_return_timezone_aware_datetime")
        return value.astimezone(timezone.utc)

    def _now(self) -> datetime:
        return self.current_time()

    def validate_ttl(self, value: int) -> int:
        """Validate a lease TTL against this service's configured bounds."""
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("invalid_lease_ttl")
        if not self._min_ttl <= value <= self._max_ttl:
            raise ValueError("lease_ttl_out_of_range")
        return value

    def _ttl(self, value: int) -> int:
        return self.validate_ttl(value)

    @staticmethod
    def _identity(value: str, field: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > 200:
            raise ValueError(f"invalid_{field}")
        return value.strip()

    def claim(self, *, workspace_id: str, task_id: str, agent_id: str,
              worker_id: str, ttl_seconds: int = 60) -> dict[str, Any]:
        workspace = self._identity(workspace_id, "workspace_id")
        task = self._identity(task_id, "task_id")
        agent = self._identity(agent_id, "agent_id")
        worker = self._identity(worker_id, "worker_id")
        ttl = self._ttl(ttl_seconds)
        if self._agent_is_active(workspace, agent) is not True:
            raise PermissionError("worker_agent_not_active")
        now = self._now()
        return self._repo.claim(
            workspace, task, agent, worker, "lease_" + uuid.uuid4().hex,
            (now + timedelta(seconds=ttl)).isoformat(),
        )

    def get_active_lease(self, *, workspace_id: str, task_id: str,
                         agent_id: str, worker_id: str) -> dict[str, Any] | None:
        """Return a verified active lease snapshot for trusted host adapters.

        The repository read is repeated after validation and the version/owner
        must remain unchanged. Renewal still uses compare-and-swap, so a race
        after this snapshot fails closed at the next heartbeat.
        """
        workspace = self._identity(workspace_id, "workspace_id")
        task = self._identity(task_id, "task_id")
        agent = self._identity(agent_id, "agent_id")
        worker = self._identity(worker_id, "worker_id")
        first = self._repo.get(workspace, task)
        if not isinstance(first, dict):
            return None
        if not self.validate(
            workspace_id=workspace, task_id=task,
            agent_id=agent, worker_id=worker,
        ):
            return None
        second = self._repo.get(workspace, task)
        if not isinstance(second, dict):
            return None
        identity = ("workspace_id", "task_id", "agent_id", "worker_id", "lease_id", "version")
        if any(first.get(key) != second.get(key) for key in identity):
            return None
        return dict(second)

    def validate(self, *, workspace_id: str, task_id: str,
                 agent_id: str, worker_id: str) -> bool:
        workspace = self._identity(workspace_id, "workspace_id")
        task = self._identity(task_id, "task_id")
        agent = self._identity(agent_id, "agent_id")
        worker = self._identity(worker_id, "worker_id")
        lease = self._repo.get(workspace, task)
        if not isinstance(lease, dict):
            return False
        if (lease.get("agent_id") != agent or lease.get("worker_id") != worker
                or lease.get("status") != "active"):
            return False
        try:
            expiry = datetime.fromisoformat(lease["expires_at"])
            if expiry.tzinfo is None or expiry.astimezone(timezone.utc) <= self._now():
                return False
        except (KeyError, TypeError, ValueError):
            return False
        return self._agent_is_active(workspace, agent) is True

    def renew(self, *, workspace_id: str, task_id: str, agent_id: str,
              worker_id: str, lease_id: str, expected_version: int,
              ttl_seconds: int = 60) -> dict[str, Any]:
        workspace = self._identity(workspace_id, "workspace_id")
        task = self._identity(task_id, "task_id")
        agent = self._identity(agent_id, "agent_id")
        worker = self._identity(worker_id, "worker_id")
        lease = self._identity(lease_id, "lease_id")
        ttl = self._ttl(ttl_seconds)
        if not self.validate(workspace_id=workspace, task_id=task,
                             agent_id=agent, worker_id=worker):
            raise PermissionError("worker_lease_not_valid")
        current = self._repo.get(workspace, task)
        if (current.get("lease_id") != lease
                or current.get("version") != expected_version):
            raise PermissionError("worker_lease_version_or_owner_mismatch")
        return self._repo.renew(
            workspace, task, lease, worker, expected_version,
            (self._now() + timedelta(seconds=ttl)).isoformat(),
        )

    def release(self, *, workspace_id: str, task_id: str,
                worker_id: str, lease_id: str,
                expected_version: int) -> dict[str, Any]:
        workspace = self._identity(workspace_id, "workspace_id")
        task = self._identity(task_id, "task_id")
        worker = self._identity(worker_id, "worker_id")
        lease = self._identity(lease_id, "lease_id")
        current = self._repo.get(workspace, task)
        if not isinstance(current, dict) or current.get("status") != "active":
            raise PermissionError("worker_lease_not_active")
        if (current.get("lease_id") != lease or current.get("worker_id") != worker
                or current.get("version") != expected_version):
            raise PermissionError("worker_lease_owner_or_version_mismatch")
        return self._repo.release(workspace, task, lease, worker, expected_version)


class WorkerLeaseHeartbeat:
    """Checkpoint-driven heartbeat for a trusted worker lease.

    Call should_continue from the execution runner's existing polling callback.
    This is deliberately not a background thread: a stalled runner cannot be
    kept alive by an independent heartbeat. Identity and initial lease must
    come from trusted host-side resolution, never request-body claims.
    """

    def __init__(self, *, service: WorkerLeaseService, lease: dict[str, Any],
                 ttl_seconds: int = 60, heartbeat_interval_seconds: int | None = None,
                 clock: Callable[[], datetime] | None = None):
        if not isinstance(lease, dict):
            raise TypeError("trusted_worker_lease_record_required")
        self._service = service
        self._workspace = WorkerLeaseService._identity(lease.get("workspace_id"), "workspace_id")
        self._task = WorkerLeaseService._identity(lease.get("task_id"), "task_id")
        self._agent = WorkerLeaseService._identity(lease.get("agent_id"), "agent_id")
        self._worker = WorkerLeaseService._identity(lease.get("worker_id"), "worker_id")
        self._lease_id = WorkerLeaseService._identity(lease.get("lease_id"), "lease_id")
        version = lease.get("version")
        if isinstance(version, bool) or not isinstance(version, int) or version < 1:
            raise ValueError("invalid_worker_lease_version")
        self._version = version
        self._ttl = service.validate_ttl(ttl_seconds)
        interval = heartbeat_interval_seconds if heartbeat_interval_seconds is not None else max(1, self._ttl // 3)
        if isinstance(interval, bool) or not isinstance(interval, int) or not 1 <= interval < self._ttl:
            raise ValueError("heartbeat_interval_must_be_positive_and_less_than_ttl")
        self._interval = interval
        self._clock = clock or service.current_time
        self._next_beat = self._now() + timedelta(seconds=interval)
        import threading
        self._lock = threading.Lock()

    def _now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError("heartbeat_clock_must_return_timezone_aware_datetime")
        return value.astimezone(timezone.utc)

    def should_continue(self) -> bool:
        """Validate each runner poll and renew only when the heartbeat is due."""
        try:
            with self._lock:
                now = self._now()
                if now >= self._next_beat:
                    renewed = self._service.renew(
                        workspace_id=self._workspace, task_id=self._task,
                        agent_id=self._agent, worker_id=self._worker,
                        lease_id=self._lease_id, expected_version=self._version,
                        ttl_seconds=self._ttl,
                    )
                    if not isinstance(renewed, dict) or renewed.get("lease_id") != self._lease_id:
                        return False
                    self._version = renewed.get("version")
                    if isinstance(self._version, bool) or not isinstance(self._version, int):
                        return False
                    self._next_beat = now + timedelta(seconds=self._interval)
                    return True
                return self._service.validate(
                    workspace_id=self._workspace, task_id=self._task,
                    agent_id=self._agent, worker_id=self._worker,
                ) is True
        except Exception:
            return False

    @property
    def current_version(self) -> int:
        return self._version


class WorkerLeaseExecutionValidator:
    """Bind immutable execution intents to authoritative worker assignments.

    resolve_assignment is a mandatory host trust root. It must authenticate the
    supplied session and resolve the intent-to-task/agent/worker assignment
    from authoritative server-side records. It must never trust assignment IDs
    supplied by an execution request. The validator checks that mapping against
    the immutable intent, resolves the live lease from WorkerLeaseService, and
    keeps one checkpoint heartbeat per intent for the duration of execution.
    """

    _ASSIGNMENT_FIELDS = (
        "intent_id", "workspace_id", "entity_id", "capability_id",
        "task_id", "agent_id", "worker_id",
    )

    def __init__(
        self, *, service: WorkerLeaseService,
        resolve_assignment: Callable[[Any, str, dict[str, Any]], dict[str, Any] | None],
        ttl_seconds: int = 60,
        heartbeat_interval_seconds: int | None = None,
        max_active_intents: int = 4096,
    ):
        if not isinstance(service, WorkerLeaseService):
            raise TypeError("worker_lease_service_required")
        if not callable(resolve_assignment):
            raise TypeError("authoritative_execution_assignment_resolver_required")
        if isinstance(max_active_intents, bool) or not isinstance(max_active_intents, int) or max_active_intents < 1:
            raise ValueError("max_active_lease_intents_must_be_positive")
        self._service = service
        self._resolve = resolve_assignment
        self._ttl = service.validate_ttl(ttl_seconds)
        self._interval = heartbeat_interval_seconds
        self._max = max_active_intents
        import threading
        self._lock = threading.RLock()
        self._heartbeats: dict[str, tuple[tuple[str, ...], WorkerLeaseHeartbeat]] = {}

    def __call__(self, session: Any, intent_id: str, intent: dict[str, Any]) -> bool:
        if not isinstance(intent_id, str) or not intent_id.strip() or not isinstance(intent, dict):
            return False
        try:
            assignment = self._resolve(session, intent_id, dict(intent))
            if not isinstance(assignment, dict):
                return False
            if any(not isinstance(assignment.get(field), str) or not assignment[field].strip()
                   for field in self._ASSIGNMENT_FIELDS):
                return False
            if assignment["intent_id"] != intent_id:
                return False
            for field in ("workspace_id", "entity_id", "capability_id"):
                if assignment[field] != intent.get(field):
                    return False

            lease = self._service.get_active_lease(
                workspace_id=assignment["workspace_id"],
                task_id=assignment["task_id"],
                agent_id=assignment["agent_id"],
                worker_id=assignment["worker_id"],
            )
            if not isinstance(lease, dict):
                return False
            identity = tuple(str(lease.get(field, "")) for field in (
                "workspace_id", "task_id", "agent_id", "worker_id", "lease_id",
            ))
            if any(not value for value in identity):
                return False

            with self._lock:
                existing = self._heartbeats.get(intent_id)
                if existing is None:
                    if len(self._heartbeats) >= self._max:
                        return False
                    heartbeat = WorkerLeaseHeartbeat(
                        service=self._service, lease=lease,
                        ttl_seconds=self._ttl,
                        heartbeat_interval_seconds=self._interval,
                    )
                    self._heartbeats[intent_id] = (identity, heartbeat)
                else:
                    old_identity, heartbeat = existing
                    if old_identity != identity:
                        return False
            return heartbeat.should_continue() is True
        except Exception:
            return False

    def forget(self, intent_id: str) -> bool:
        """Release in-memory heartbeat state after the host confirms termination."""
        if not isinstance(intent_id, str) or not intent_id.strip():
            return False
        with self._lock:
            return self._heartbeats.pop(intent_id, None) is not None
