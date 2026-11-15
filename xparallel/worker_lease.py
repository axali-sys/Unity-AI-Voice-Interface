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

    def _now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None:
            raise ValueError("lease_clock_must_return_timezone_aware_datetime")
        return value.astimezone(timezone.utc)

    def _ttl(self, value: int) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("invalid_lease_ttl")
        if not self._min_ttl <= value <= self._max_ttl:
            raise ValueError("lease_ttl_out_of_range")
        return value

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
