from datetime import datetime, timedelta, timezone
import os
import tempfile
import unittest

from xparallel.worker_lease import WorkerLeaseService
from xparallel.sqlite_worker_lease_repository import SQLiteWorkerLeaseRepository


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
        if old and old["status"] == "active" and datetime.fromisoformat(old["expires_at"]) > datetime(2026, 1, 1, tzinfo=timezone.utc):
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


class WorkerLeaseTests(unittest.TestCase):
    def make_service(self, active=lambda workspace, agent: True):
        clock = Clock()
        repo = MemoryLeaseRepository()
        service = WorkerLeaseService(repository=repo, agent_is_active=active, clock=clock)
        return service, repo, clock

    def test_claim_validate_renew_and_release_lease(self):
        service, repo, clock = self.make_service()
        lease = service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                              worker_id="worker-1", ttl_seconds=60)
        self.assertTrue(service.validate(workspace_id="w1", task_id="t1",
                                         agent_id="a1", worker_id="worker-1"))
        renewed = service.renew(workspace_id="w1", task_id="t1", agent_id="a1",
                                worker_id="worker-1", lease_id=lease["lease_id"],
                                expected_version=lease["version"], ttl_seconds=90)
        self.assertEqual(renewed["version"], 2)
        released = service.release(workspace_id="w1", task_id="t1",
                                   worker_id="worker-1", lease_id=lease["lease_id"],
                                   expected_version=renewed["version"])
        self.assertEqual(released["status"], "released")
        self.assertFalse(service.validate(workspace_id="w1", task_id="t1",
                                          agent_id="a1", worker_id="worker-1"))

    def test_revoked_agent_cannot_validate_or_renew_lease(self):
        active = {"value": True}
        service, repo, clock = self.make_service(lambda workspace, agent: active["value"])
        lease = service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                              worker_id="worker-1")
        active["value"] = False
        self.assertFalse(service.validate(workspace_id="w1", task_id="t1",
                                           agent_id="a1", worker_id="worker-1"))
        with self.assertRaisesRegex(PermissionError, "worker_lease_not_valid"):
            service.renew(workspace_id="w1", task_id="t1", agent_id="a1",
                          worker_id="worker-1", lease_id=lease["lease_id"],
                          expected_version=lease["version"])

    def test_expired_lease_is_not_valid(self):
        service, repo, clock = self.make_service()
        service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                      worker_id="worker-1", ttl_seconds=15)
        clock.value += timedelta(seconds=16)
        self.assertFalse(service.validate(workspace_id="w1", task_id="t1",
                                          agent_id="a1", worker_id="worker-1"))

    def test_workspace_and_worker_isolation(self):
        service, repo, clock = self.make_service()
        service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                      worker_id="worker-1")
        self.assertFalse(service.validate(workspace_id="w2", task_id="t1",
                                           agent_id="a1", worker_id="worker-1"))
        self.assertFalse(service.validate(workspace_id="w1", task_id="t1",
                                           agent_id="a1", worker_id="worker-2"))

    def test_invalid_ttl_and_naive_clock_are_rejected(self):
        service, repo, clock = self.make_service()
        with self.assertRaisesRegex(ValueError, "lease_ttl_out_of_range"):
            service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                          worker_id="worker-1", ttl_seconds=1)
        clock.value = datetime(2026, 1, 1)
        with self.assertRaisesRegex(ValueError, "timezone_aware"):
            service.claim(workspace_id="w1", task_id="t1", agent_id="a1",
                          worker_id="worker-1")


    def test_sqlite_repository_persists_leases_and_audit_events(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "leases.sqlite3")
            repo = SQLiteWorkerLeaseRepository(path)
            expires = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
            lease = repo.claim("w1", "t1", "a1", "worker-1", "lease-1", expires)
            reopened = SQLiteWorkerLeaseRepository(path)
            self.assertEqual(reopened.get("w1", "t1")["lease_id"], lease["lease_id"])
            with self.assertRaisesRegex(PermissionError, "already_claimed"):
                reopened.claim("w1", "t1", "a2", "worker-2", "lease-2", expires)
            renewed = reopened.renew("w1", "t1", "lease-1", "worker-1", 1,
                                     (datetime.now(timezone.utc) + timedelta(seconds=90)).isoformat())
            self.assertEqual(renewed["version"], 2)
            with self.assertRaisesRegex(PermissionError, "stale"):
                repo.renew("w1", "t1", "lease-1", "worker-1", 1,
                           (datetime.now(timezone.utc) + timedelta(seconds=90)).isoformat())
            released = repo.release("w1", "t1", "lease-1", "worker-1", 2)
            self.assertEqual(released["status"], "released")
            events = reopened.list_events("w1", "t1")
            self.assertEqual([event["event_type"] for event in events],
                             ["lease_released", "lease_renewed", "lease_claimed"])

    def test_sqlite_repository_reclaims_expired_lease_with_new_version(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteWorkerLeaseRepository(os.path.join(directory, "leases.sqlite3"))
            expired = (datetime.now(timezone.utc) - timedelta(seconds=2)).isoformat()
            repo.claim("w1", "t1", "a1", "worker-1", "lease-old",
                       (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat())
            # Force expiry through a separate direct test-fixture update.
            import sqlite3
            with sqlite3.connect(repo.path) as db:
                db.execute("UPDATE worker_leases SET expires_at=? WHERE workspace_id=? AND task_id=?",
                           (expired, "w1", "t1"))
            replacement = repo.claim("w1", "t1", "a2", "worker-2", "lease-new",
                                      (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat())
            self.assertEqual(replacement["lease_id"], "lease-new")
            self.assertEqual(replacement["version"], 2)
            self.assertEqual(repo.list_events("w1", "t1")[0]["event_type"], "lease_reclaimed")


if __name__ == "__main__":
    unittest.main()
