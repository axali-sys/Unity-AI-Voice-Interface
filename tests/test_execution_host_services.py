import unittest

from xparallel.execution_host_services import ExecutionHostServices


class FakeApprovals:
    def start(self, session, ticket): return {}
    def check_running(self, session, intent_id): return {"continue": True}
    def begin_finalization(self, session, intent_id, *, outcome): return {"status": "finalizing"}
    def complete_finalization(self, session, intent_id): return {"status": "completed"}
    def set_receipt_commit_verifier(self, verifier): self.receipt_verifier = verifier
    def get_finalization_for_recovery(self, session, intent_id): return {"status": "finalizing", "finalization_data": {}}


class FakeReceipts:
    def verify_committed_receipt(self, *args, **kwargs): return True
    def get_by_intent(self, *args, **kwargs): return None
    def append(self, *args, **kwargs): return {}


class ExecutionHostServicesTests(unittest.TestCase):
    def setUp(self):
        self.intent = {"artifact_digest": "a" * 64, "limits": {
            "timeout_seconds": 30, "memory_mb": 256, "cpu_millis": 1000, "output_bytes": 4096, "pids": 32,
        }}
        self.services = ExecutionHostServices(
            approvals=FakeApprovals(), runner=lambda *a, **k: {"status": "success"},
            load_payload=lambda intent: {"files": {"main.py": "eA=="}},
            resolve_artifact_digest=lambda intent: "a" * 64,
            resolve_policy_evidence=lambda intent: {
                "allowed": True, "grant_id": "grant:1", "evidence_run_id": "run:1",
            },
            measure_resources=lambda result, intent: {
                "wall_ms": 100, "cpu_ms": 20, "memory_peak_mb": 64,
                "output_bytes": 10, "pids_peak": 1,
            },
            store_evidence=lambda result, intent: {
                "durable": True, "references": ["evidence://workspace/job/1"],
            },
            receipts=FakeReceipts(),
        )

    def test_builds_worker_only_with_complete_host_dependencies(self):
        from xparallel.execution_worker import ApprovedExecutionWorker
        self.assertIsInstance(self.services.build_worker(), ApprovedExecutionWorker)

    def test_rejects_artifact_mismatch(self):
        self.services._resolve_artifact = lambda intent: "b" * 64
        with self.assertRaisesRegex(PermissionError, "artifact_digest_mismatch"):
            self.services.resolve_artifact_digest(self.intent)

    def test_rejects_policy_without_authoritative_evidence_ids(self):
        self.services._resolve_policy = lambda intent: {"allowed": True}
        with self.assertRaisesRegex(ValueError, "grant_id_required"):
            self.services.resolve_policy_evidence(self.intent)

    def test_rejects_incomplete_or_untrusted_resource_metrics(self):
        self.services._measure = lambda result, intent: {"wall_ms": 10}
        with self.assertRaisesRegex(ValueError, "complete_host_resource_measurement"):
            self.services.measure_resources({}, self.intent)

        self.services._measure = lambda result, intent: {
            "wall_ms": True, "cpu_ms": 1, "memory_peak_mb": 1,
            "output_bytes": 1, "pids_peak": 1,
        }
        with self.assertRaisesRegex(ValueError, "invalid_host_resource_measurement"):
            self.services.measure_resources({}, self.intent)

    def test_rejects_usage_over_approved_limits(self):
        self.services._measure = lambda result, intent: {
            "wall_ms": 31000, "cpu_ms": 1, "memory_peak_mb": 1,
            "output_bytes": 1, "pids_peak": 1,
        }
        with self.assertRaisesRegex(ValueError, "exceeds_approved_limits"):
            self.services.measure_resources({}, self.intent)


    def test_rejects_cpu_usage_above_approved_quota(self):
        self.services._measure = lambda result, intent: {
            "wall_ms": 1000, "cpu_ms": 1001, "memory_peak_mb": 1,
            "output_bytes": 1, "pids_peak": 1,
        }
        with self.assertRaisesRegex(ValueError, "exceeds_approved_limits"):
            self.services.measure_resources({}, self.intent)

    def test_requires_explicit_durable_evidence_acknowledgement(self):
        self.services._store = lambda result, intent: {
            "durable": False, "references": ["evidence://temporary"],
        }
        with self.assertRaisesRegex(ValueError, "durable_execution_evidence_storage"):
            self.services.store_evidence({}, self.intent)


if __name__ == "__main__":
    unittest.main()
