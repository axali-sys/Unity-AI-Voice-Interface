import tempfile
import unittest
from pathlib import Path

from xparallel.governance_bootstrap import build_entity_governance


class GovernanceBootstrapTests(unittest.TestCase):
    def test_disabled_by_default(self):
        self.assertIsNone(build_entity_governance(lambda token: {} , environ={}))

    def test_requires_both_explicit_database_paths(self):
        env = {"XP_GOVERNANCE_ENABLE": "true", "XP_DNA_DB_PATH": "/tmp/dna.sqlite3"}
        self.assertIsNone(build_entity_governance(lambda token: {}, environ=env))

    def test_rejects_relative_database_paths(self):
        env = {
            "XP_GOVERNANCE_ENABLE": "1",
            "XP_DNA_DB_PATH": "dna.sqlite3",
            "XP_GOVERNANCE_DB_PATH": "/tmp/governance.sqlite3",
        }
        with self.assertRaisesRegex(ValueError, "absolute"):
            build_entity_governance(lambda token: {}, environ=env)

    def test_creates_registry_only_with_explicit_host_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            env = {
                "XP_GOVERNANCE_ENABLE": "1",
                "XP_DNA_DB_PATH": str(Path(directory) / "dna.sqlite3"),
                "XP_GOVERNANCE_DB_PATH": str(Path(directory) / "governance.sqlite3"),
            }
            verifier = lambda token: {
                "authenticated": True, "subject": "owner-1",
                "workspace_id": "workspace-1", "role": "owner",
            }
            registry = build_entity_governance(verifier, environ=env)
            self.assertIsNotNone(registry)
            registry.close()


if __name__ == "__main__":
    unittest.main()
