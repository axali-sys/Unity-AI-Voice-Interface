import hashlib
import tempfile
import unittest
from pathlib import Path

from xparallel.capability_verification import CapabilityVerificationLab
from xparallel.digital_dna import DigitalDNARegistry
from xparallel.entity_governance import EntityGovernanceRegistry
from xparallel.identity_trust import EntityKeyStore
from xparallel.trusted_host_adapters import TrustedHostAdapters


class TrustedHostAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.owner = {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-a"}
        self.dna = DigitalDNARegistry(str(root / "dna.sqlite3"))
        self.keys = EntityKeyStore(str(root / "keys.sqlite3"))
        self.governance = EntityGovernanceRegistry(
            authenticate=lambda session: self.owner if session == "valid" else {"authenticated": False},
            resolve_owner=lambda workspace, entity: "owner:1" if (workspace, entity) == ("ws-a", "entity-1234") else None,
            authorize_governance=lambda principal, entity, operation: principal["subject"] == "governor:1",
            db_path=str(root / "governance.sqlite3"),
        )
        self.lab = CapabilityVerificationLab(
            authenticate=lambda session: self.owner if session == "valid" else {"authenticated": False},
            authorize_verifier=lambda principal, entity, capability, operation: True,
            resolve_test_plan=lambda plan, version, entity, capability: {
                "plan_id": plan, "version": version, "case_ids": ["case.one"]
            },
            execute_tests=lambda *args: {"cases": [{
                "case_id": "case.one", "status": "pass", "evidence_ref": "evidence:one"
            }]},
            db_path=str(root / "verification.sqlite3"),
        )
        self.digest = hashlib.sha256(b"trusted-build-artifact").hexdigest()
        self.manifest = {
            "schema_version": "0.1.0", "entity_id": "entity-1234",
            "entity_type": "agent", "display_name": "Test Entity", "issuer": "test",
            "status": "pending", "created_at": "2026-01-01T00:00:00+00:00",
            "updated_at": "2026-01-01T00:00:00+00:00",
            "owner": {"subject": "owner:1"}, "protocols": [{"id": "xparallel", "version": "1.0.0"}],
            "capabilities": [{
                "capability_id": "research.read", "version": "1.0.0", "purpose": "test",
                "status": "declared", "evidence_refs": [], "required_scopes": ["doc:7"],
            }],
            "permission_requests": [],
            "data_handling": {"memory_classes": [], "retention_policy": "test"},
        }
        self.dna.register("ws-a", self.manifest)
        self.keys.register_pending_key("ws-a", "entity-1234", "key-a", self._public_key())
        # Activate a test key through the actual proof-of-possession flow.
        self._activate_key()
        self.adapters = TrustedHostAdapters(
            authenticate=lambda session: self.owner if session == "valid" else {"authenticated": False},
            dna_registry=self.dna, key_store=self.keys, governance=self.governance,
            verification_lab=self.lab,
            resolve_artifact=lambda ws, entity, cap, version: {
                "version": version, "artifact_digest": self.digest
            } if ws == "ws-a" and entity == "entity-1234" and cap == "research.read" else None,
        )

    def _public_key(self):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        import base64
        self.private_key = Ed25519PrivateKey.generate()
        raw = self.private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw).decode("ascii")

    def _activate_key(self):
        import base64
        from xparallel.identity_trust import owner_challenge_message
        challenge = self.keys.create_owner_challenge("ws-a", "entity-1234", "key-a")
        message = base64.b64decode(challenge["message_b64"])
        signature = self.private_key.sign(message)
        self.keys.verify_owner_challenge(
            "ws-a", "entity-1234", "key-a", challenge["challenge_id"],
            base64.b64encode(signature).decode("ascii"),
        )

    def tearDown(self):
        self.lab.close()
        self.governance.close()
        self.keys.close()
        self.dna.close()
        self.temp.cleanup()

    def test_authenticated_context_uses_registry_key_and_trusted_artifact(self):
        principal = self.adapters.authenticate("valid")
        context = self.adapters.resolve_entity_context(
            principal, "entity-1234", "key-a", "research.read"
        )
        self.assertEqual(context["owner_subject"], "owner:1")
        self.assertEqual(context["entity_status"], "pending")
        self.assertEqual(context["key_status"], "active")
        self.assertEqual(context["artifact_digest"], self.digest)

    def test_untrusted_or_incomplete_authentication_fails_closed(self):
        self.assertEqual(self.adapters.authenticate("invalid"), {"authenticated": False})
        with self.assertRaises(PermissionError):
            self.adapters.authenticate({"subject": "owner:1", "workspace_id": "ws-a"})

    def test_workspace_and_entity_key_lookup_are_scoped(self):
        principal = {"authenticated": True, "subject": "owner:1", "workspace_id": "ws-other"}
        with self.assertRaises(LookupError):
            self.adapters.resolve_entity_context(principal, "entity-1234", "key-a", "research.read")

    def test_manifest_cannot_supply_verified_artifact_digest(self):
        self.manifest["capabilities"][0]["artifact_digest"] = "f" * 64
        # Registry is immutable by revision; submit a new revision with the same declared claim.
        self.dna.revise("ws-a", "entity-1234", self.manifest, expected_revision=1)
        self.adapters._resolve_artifact = lambda *args: None
        with self.assertRaises(LookupError):
            self.adapters.resolve_entity_context(
                self.owner, "entity-1234", "key-a", "research.read"
            )

    def test_wrong_key_or_missing_capability_is_rejected(self):
        with self.assertRaises(LookupError):
            self.adapters.resolve_entity_context(
                self.owner, "entity-1234", "missing-key", "research.read"
            )
        with self.assertRaises(LookupError):
            self.adapters.resolve_entity_context(
                self.owner, "entity-1234", "key-a", "admin.execute"
            )

    def test_gate_factory_keeps_authentication_and_workspace_server_side(self):
        gate = self.adapters.build_action_gate()
        denied = gate.authorize(
            "invalid", entity_id="entity-1234", key_id="key-a",
            capability_id="research.read", action="read", resource_scope="doc:7",
        )
        self.assertFalse(denied["allowed"])
        self.assertEqual(denied["reason"], "caller_not_authenticated")


if __name__ == "__main__":
    unittest.main()
