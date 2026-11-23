import unittest

from xparallel.authz import authorize


class MemoryRecoveryAuthorizationTests(unittest.TestCase):
    def test_backup_requires_authenticated_role(self):
        self.assertTrue(authorize("operator", "memory_backup"))
        self.assertFalse(authorize("viewer", "memory_backup"))

    def test_recovery_is_owner_only(self):
        self.assertTrue(authorize("owner", "memory_recover"))
        self.assertFalse(authorize("admin", "memory_recover"))
        self.assertFalse(authorize("operator", "memory_recover"))
        self.assertFalse(authorize("viewer", "memory_recover"))


if __name__ == "__main__":
    unittest.main()
