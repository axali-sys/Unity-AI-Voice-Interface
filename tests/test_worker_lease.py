from datetime import datetime, timedelta, timezone

import pytest

from xparallel.worker_lease import WorkerLeaseService


class Clock:
    def __init__(self):
        self.value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self):
        return self.value


class MemoryLeaseRepository:
    def __init__(self):
        self.rows = {}

    def claim(self, workspace, task, agent, worker, lease_id, expires_at):
        key = (workspace, task)
        old = self.rows.get(key)
        if old and old["status"] == "active" and datetime.fromisoformat(old["expires_at"]) > datetime.now(timezone.utc):
            raise ValueError("lease_already_claimed")
        row = {"workspace_id": workspace, "task_id": task, "agent_id": agent,
               "worker_id": worker, "lease_id": lease_id, "expires_at": expires_at,
               "status": "active", "version": 1}
        self.rows[key] = row
        return dict(row)

    def get(self, workspace, task):
        row = self.rows.get((workspace, task))
        return dict(row) if row else None

    def renew(self, workspace, task, lease_id, worker, expected_version, expires_at):
        row = self.rows[(workspace, task)]
        if row["lease_id"] != lease_id or row["worker_id"] != worker or row["version"] != expected_version:
            raise ValueError("stale_lease")
        row.update(expires_at=expires_at, version=row["version"] + 1)
        return dict(row)

    def release(self, workspace, task, lease_id, worker, expected_version):
        row = self.rows[(workspace, task)]
        if row["lease_id"] != lease_id or row["worker_id"] != worker or row["version"] != expected_version:
            raise ValueError("stale_lease")
        row.update(status="released", version=row["version"] + 1)
        return dict(row)


def make_service(active=lambda workspace, agent: True):
    clock = Clock()
    repo = MemoryLeaseRepository()
    service = WorkerLeaseService(repository=repo, agent_is_active=active, clock=clock)
    return service, repo, clock


def test_claim_validate_renew_and_release_lease():
    service, repo, clock = make_service()
    lease = service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                          worker_id="worker-1", ttl_seconds=60)
    assert service.validate(workspace_id="w1", task_id="t1",
                            agent_id="a1", worker_id="worker-1")
    renewed = service.renew(workspace_id="w1", task_id="t1", agent_id="a1",
                            worker_id="worker-1", lease_id=lease["lease_id"],
                            expected_version=lease["version"], ttl_seconds=90)
    assert renewed["version"] == 2
    released = service.release(workspace_id="w1", task_id="t1",
                               worker_id="worker-1", lease_id=lease["lease_id"],
                               expected_version=renewed["version"])
    assert released["status"] == "released"
    assert not service.validate(workspace_id="w1", task_id="t1",
                                agent_id="a1", worker_id="worker-1")


def test_revoked_agent_cannot_validate_or_renew_lease():
    active = {"value": True}
    service, repo, clock = make_service(lambda workspace, agent: active["value"])
    lease = service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                          worker_id="worker-1")
    active["value"] = False
    assert not service.validate(workspace_id="w1", task_id="t1",
                                 agent_id="a1", worker_id="worker-1")
    with pytest.raises(PermissionError, match="worker_lease_not_valid"):
        service.renew(workspace_id="w1", task_id="t1", agent_id="a1",
                      worker_id="worker-1", lease_id=lease["lease_id"],
                      expected_version=lease["version"])


def test_expired_lease_is_not_valid():
    service, repo, clock = make_service()
    service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                  worker_id="worker-1", ttl_seconds=15)
    clock.value += timedelta(seconds=16)
    assert not service.validate(workspace_id="w1", task_id="t1",
                                agent_id="a1", worker_id="worker-1")


def test_lease_cannot_be_validated_from_another_workspace_or_worker():
    service, repo, clock = make_service()
    service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                  worker_id="worker-1")
    assert not service.validate(workspace_id="w2", task_id="t1",
                                agent_id="a1", worker_id="worker-1")
    assert not service.validate(workspace_id="w1", task_id="t1",
                                agent_id="a1", worker_id="worker-2")


def test_invalid_ttl_and_naive_clock_are_rejected():
    service, repo, clock = make_service()
    with pytest.raises(ValueError, match="lease_ttl_out_of_range"):
        service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                      worker_id="worker-1", ttl_seconds=1)
    clock.value = datetime(2026, 1, 1)
    with pytest.raises(ValueError, match="timezone_aware"):
        service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                      worker_id="worker-1")
