import copy
import tempfile
import unittest
from pathlib import Path

from xparallel.digital_dna import DigitalDNARegistry, validate_manifest


def manifest():
    return {
        "schema_version": "0.1.0",
        "entity_id": "xp:example:agent-001",
        "entity_type": "agent",
        "display_name": "Example Agent",
        "issuer": "xp:test-registry",
        "status": "pending",
        "created_at": "2026-11-13T00:00:00Z",
        "updated_at": "2026-11-13T00:00:00Z",
        "owner": {"subject": "workspace:alpha"},
        "protocols": [{"id": "xparallel.entity-message", "version": "0.1.0"}],
        "capabilities": [{
            "capability_id": "research.summarize",
            "version": "0.1.0",
            "purpose": "Summarize user-provided public sources.",
            "status": "declared",
            "evidence_refs": [],
            "required_scopes": ["research.read"],
        }],
        "permission_requests": [{
            "action": "read",
            "resource_scope": "user-supplied-public-sources",
        }],
        "data_handling": {
            "memory_classes": ["ephemeral-task-context"],
            "retention_policy": "Discard at task completion.",
        },
    }


class DigitalDNARegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "dna.sqlite3")
        self.registry = DigitalDNARegistry(self.db)

    def tearDown(self):
        self.registry.close()
        self.temp.cleanup()

    def test_register_and_retrieve_manifest(self):
        created = self.registry.register("alpha", manifest())
        loaded = self.registry.get("alpha", created["entity_id"])
        self.assertEqual(loaded["manifest"], manifest())
        self.assertEqual(loaded["revision"], 1)
        self.assertEqual(len(loaded["manifest_digest"]), 64)

    def test_duplicate_registration_is_rejected(self):
        self.registry.register("alpha", manifest())
        with self.assertRaisesRegex(ValueError, "entity_already_registered"):
            self.registry.register("alpha", manifest())

    def test_workspaces_are_isolated(self):
        self.registry.register("alpha", manifest())
        self.assertIsNone(self.registry.get("beta", "xp:example:agent-001"))
        self.assertEqual(self.registry.list("beta"), [])

    def test_revision_is_append_only_and_retrievable(self):
        original = manifest()
        self.registry.register("alpha", original)
        revised = copy.deepcopy(original)
        revised["display_name"] = "Updated Agent"
        revised["updated_at"] = "2026-11-13T01:00:00Z"
        result = self.registry.revise("alpha", revised["entity_id"], revised, 1)
        self.assertEqual(result["revision"], 2)
        self.assertEqual(self.registry.get("alpha", revised["entity_id"], 1)["manifest"], original)
        self.assertEqual(self.registry.get("alpha", revised["entity_id"])["manifest"]["display_name"], "Updated Agent")

    def test_revision_conflict_is_rejected(self):
        original = manifest()
        self.registry.register("alpha", original)
        revised = copy.deepcopy(original)
        revised["display_name"] = "Changed"
        revised["updated_at"] = "2026-11-13T01:00:00Z"
        with self.assertRaisesRegex(ValueError, "revision_conflict"):
            self.registry.revise("alpha", revised["entity_id"], revised, 4)

    def test_owner_change_requires_separate_transfer_flow(self):
        original = manifest()
        self.registry.register("alpha", original)
        revised = copy.deepcopy(original)
        revised["owner"]["subject"] = "workspace:other"
        revised["updated_at"] = "2026-11-13T01:00:00Z"
        with self.assertRaisesRegex(ValueError, "owner_transfer_requires_separate_verified_flow"):
            self.registry.revise("alpha", revised["entity_id"], revised, 1)

    def test_rejects_unknown_schema_and_invalid_semver(self):
        invalid = manifest()
        invalid["schema_version"] = "9.0.0"
        with self.assertRaisesRegex(ValueError, "unsupported_schema_version"):
            validate_manifest(invalid)
        invalid = manifest()
        invalid["protocols"][0]["version"] = "v0.1"
        with self.assertRaisesRegex(ValueError, "invalid_protocol_version"):
            validate_manifest(invalid)

    def test_registry_rejects_self_activated_entity(self):
        invalid = manifest()
        invalid["status"] = "active"
        with self.assertRaisesRegex(ValueError, "registry_submission_must_be_pending"):
            self.registry.register("alpha", invalid)

    def test_registry_rejects_self_certified_capability(self):
        invalid = manifest()
        invalid["capabilities"][0]["status"] = "verified"
        with self.assertRaisesRegex(ValueError, "capabilities_cannot_self_certify"):
            self.registry.register("alpha", invalid)

    def test_rejects_secret_material_in_manifest(self):
        invalid = manifest()
        invalid["runtime"] = {"api_key": "must-not-be-here"}
        with self.assertRaisesRegex(ValueError, "secret_field_not_allowed"):
            validate_manifest(invalid)


if __name__ == "__main__":
    unittest.main()
