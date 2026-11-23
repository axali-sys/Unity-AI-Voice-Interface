import unittest

from xparallel.memory_continuity import (
    LifecycleRequest, MemoryClass, Operation, audit_metadata, decide,
)


class MemoryContinuityPolicyTests(unittest.TestCase):
    def test_execution_reset_is_scoped_to_ephemeral_state(self):
        decision = decide(LifecycleRequest(Operation.RESET_EXECUTION))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, "clear_ephemeral_execution_only")

    def test_transform_requires_verified_source_and_result(self):
        self.assertFalse(decide(LifecycleRequest(
            Operation.TRANSFORM, source_verified=False, result_verified=True
        )).allowed)
        self.assertFalse(decide(LifecycleRequest(
            Operation.TRANSFORM, source_verified=True, result_verified=False
        )).allowed)
        self.assertTrue(decide(LifecycleRequest(
            Operation.TRANSFORM, source_verified=True, result_verified=True
        )).allowed)

    def test_erasure_requires_authorization_and_scope(self):
        self.assertFalse(decide(LifecycleRequest(
            Operation.ERASE, authorized=True, explicit_scope=False
        )).allowed)
        self.assertFalse(decide(LifecycleRequest(
            Operation.ERASE, authorized=False, explicit_scope=True
        )).allowed)

    def test_protected_memory_is_not_erased_without_expired_retention(self):
        request = LifecycleRequest(
            Operation.ERASE, memory_class=MemoryClass.IDENTITY,
            authorized=True, explicit_scope=True, retention_expired=False,
        )
        self.assertFalse(decide(request).allowed)

    def test_authorized_expired_memory_can_be_erased_in_scope(self):
        request = LifecycleRequest(
            Operation.ERASE, memory_class=MemoryClass.IDENTITY,
            authorized=True, explicit_scope=True, retention_expired=True,
        )
        self.assertTrue(decide(request).allowed)

    def test_recovery_requires_verified_source(self):
        self.assertFalse(decide(LifecycleRequest(
            Operation.RECOVER, source_verified=False
        )).allowed)
        self.assertTrue(decide(LifecycleRequest(
            Operation.RECOVER, source_verified=True
        )).allowed)

    def test_audit_metadata_does_not_contain_payload(self):
        request = LifecycleRequest(Operation.CONSERVE)
        record = audit_metadata(request, decide(request))
        self.assertNotIn("content", record)
        self.assertNotIn("secret", record)


if __name__ == "__main__":
    unittest.main()
