import base64
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xparallel.identity_trust import (
    EntityKeyStore, owner_challenge_message, revocation_message, rotation_message,
)


def public_b64(private_key):
    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


class EntityKeyStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / "keys.sqlite3")
        self.authority = Ed25519PrivateKey.generate()
        self.store = EntityKeyStore(self.path, public_b64(self.authority))
        self.owner = Ed25519PrivateKey.generate()
        self.workspace = "workspace-a"
        self.entity = "xp:entity:sample"

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def register_and_activate(self, key_id, private_key):
        pub = public_b64(private_key)
        self.store.register_pending_key(self.workspace, self.entity, key_id, pub)
        challenge = self.store.create_owner_challenge(self.workspace, self.entity, key_id)
        message = base64.b64decode(challenge["message_b64"])
        signature = base64.b64encode(private_key.sign(message)).decode("ascii")
        self.store.verify_owner_challenge(
            self.workspace, self.entity, key_id, challenge["challenge_id"], signature
        )
        return pub

    def test_valid_owner_proof_activates_key_and_challenge_is_one_time(self):
        self.store.register_pending_key(self.workspace, self.entity, "key-1", public_b64(self.owner))
        challenge = self.store.create_owner_challenge(self.workspace, self.entity, "key-1")
        signature = base64.b64encode(
            self.owner.sign(base64.b64decode(challenge["message_b64"]))
        ).decode("ascii")
        result = self.store.verify_owner_challenge(
            self.workspace, self.entity, "key-1", challenge["challenge_id"], signature
        )
        self.assertEqual(result["status"], "active")
        with self.assertRaisesRegex(ValueError, "challenge_already_used"):
            self.store.verify_owner_challenge(
                self.workspace, self.entity, "key-1", challenge["challenge_id"], signature
            )

    def test_wrong_signature_does_not_activate_key(self):
        self.store.register_pending_key(self.workspace, self.entity, "key-1", public_b64(self.owner))
        challenge = self.store.create_owner_challenge(self.workspace, self.entity, "key-1")
        other = Ed25519PrivateKey.generate()
        signature = base64.b64encode(other.sign(base64.b64decode(challenge["message_b64"]))).decode("ascii")
        with self.assertRaisesRegex(ValueError, "signature_verification_failed"):
            self.store.verify_owner_challenge(
                self.workspace, self.entity, "key-1", challenge["challenge_id"], signature
            )
        self.assertEqual(self.store.get_key(self.workspace, self.entity, "key-1")["status"], "pending")

    def test_key_material_is_scoped_by_workspace(self):
        self.register_and_activate("key-1", self.owner)
        self.assertIsNone(self.store.get_key("workspace-b", self.entity, "key-1"))

    def test_rotation_requires_both_old_key_authority_and_new_key_proof(self):
        self.register_and_activate("old", self.owner)
        new_private = Ed25519PrivateKey.generate()
        new_public = public_b64(new_private)
        self.store.register_pending_key(self.workspace, self.entity, "new", new_public)
        challenge = self.store.create_owner_challenge(self.workspace, self.entity, "new")
        old_message = rotation_message(
            self.workspace, self.entity, "old", "new", new_public, challenge["challenge_id"]
        )
        old_sig = base64.b64encode(self.owner.sign(old_message)).decode("ascii")
        new_sig = base64.b64encode(
            new_private.sign(base64.b64decode(challenge["message_b64"]))
        ).decode("ascii")
        result = self.store.rotate_key(
            self.workspace, self.entity, "old", "new", new_public,
            challenge["challenge_id"], old_sig, new_sig,
        )
        self.assertEqual(result["old_status"], "rotated")
        self.assertEqual(self.store.get_key(self.workspace, self.entity, "new")["status"], "active")

    def test_rotation_rejects_invalid_old_key_signature(self):
        self.register_and_activate("old", self.owner)
        new_private = Ed25519PrivateKey.generate()
        new_public = public_b64(new_private)
        self.store.register_pending_key(self.workspace, self.entity, "new", new_public)
        challenge = self.store.create_owner_challenge(self.workspace, self.entity, "new")
        other = Ed25519PrivateKey.generate()
        old_sig = base64.b64encode(other.sign(rotation_message(
            self.workspace, self.entity, "old", "new", new_public, challenge["challenge_id"]
        ))).decode("ascii")
        new_sig = base64.b64encode(
            new_private.sign(base64.b64decode(challenge["message_b64"]))
        ).decode("ascii")
        with self.assertRaisesRegex(ValueError, "signature_verification_failed"):
            self.store.rotate_key(self.workspace, self.entity, "old", "new", new_public,
                                  challenge["challenge_id"], old_sig, new_sig)

    def test_authority_signed_revocation(self):
        self.register_and_activate("key-1", self.owner)
        issued = datetime.now(timezone.utc).isoformat()
        message = revocation_message(self.workspace, self.entity, "key-1", "compromised", issued)
        signature = base64.b64encode(self.authority.sign(message)).decode("ascii")
        result = self.store.revoke_key(self.workspace, self.entity, "key-1",
                                       "compromised", issued, signature)
        self.assertEqual(result["status"], "revoked")

    def test_revocation_fails_without_authority_signature(self):
        self.register_and_activate("key-1", self.owner)
        issued = datetime.now(timezone.utc).isoformat()
        message = revocation_message(self.workspace, self.entity, "key-1", "compromised", issued)
        signature = base64.b64encode(self.owner.sign(message)).decode("ascii")
        with self.assertRaisesRegex(ValueError, "signature_verification_failed"):
            self.store.revoke_key(self.workspace, self.entity, "key-1",
                                  "compromised", issued, signature)


if __name__ == "__main__":
    unittest.main()
