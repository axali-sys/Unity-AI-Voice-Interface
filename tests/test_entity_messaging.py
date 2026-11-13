import base64
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xparallel.entity_messaging import EntityMessageService
from xparallel.identity_trust import EntityKeyStore


def public_b64(private_key):
    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


class EntityMessagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.key_store = EntityKeyStore(str(Path(self.temp.name) / "keys.sqlite3"))
        self.service = EntityMessageService(
            self.key_store, str(Path(self.temp.name) / "messages.sqlite3")
        )
        self.workspace = "workspace-a"
        self.sender = "xp:sender"
        self.recipient = "xp:recipient"
        self.key_id = "sender-key-1"
        self.private = Ed25519PrivateKey.generate()
        self.key_store.register_pending_key(
            self.workspace, self.sender, self.key_id, public_b64(self.private)
        )
        challenge = self.key_store.create_owner_challenge(
            self.workspace, self.sender, self.key_id
        )
        signature = base64.b64encode(
            self.private.sign(base64.b64decode(challenge["message_b64"]))
        ).decode("ascii")
        self.key_store.verify_owner_challenge(
            self.workspace, self.sender, self.key_id,
            challenge["challenge_id"], signature
        )

    def tearDown(self):
        self.service.close()
        self.key_store.close()
        self.temp.cleanup()

    def make_message(self):
        return self.service.create_message(
            self.workspace, self.sender, self.key_id, self.recipient,
            "entity.notice", {"text": "hello", "sequence": 1}, self.private
        )

    def test_valid_signed_message_is_accepted(self):
        result = self.service.verify_and_accept(
            self.make_message(), self.workspace, self.recipient
        )
        self.assertTrue(result["accepted"])
        self.assertEqual(result["body"]["text"], "hello")

    def test_tampered_body_is_rejected(self):
        message = self.make_message()
        message["body"]["text"] = "tampered"
        with self.assertRaisesRegex(ValueError, "message_body_digest_mismatch"):
            self.service.verify_and_accept(message, self.workspace, self.recipient)

    def test_signed_header_tampering_is_rejected(self):
        message = self.make_message()
        message["message_type"] = "entity.command"
        with self.assertRaisesRegex(ValueError, "message_signature_invalid"):
            self.service.verify_and_accept(message, self.workspace, self.recipient)

    def test_recipient_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "message_recipient_mismatch"):
            self.service.verify_and_accept(self.make_message(), self.workspace, "xp:other")

    def test_workspace_mismatch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "message_workspace_mismatch"):
            self.service.verify_and_accept(self.make_message(), "workspace-b", self.recipient)

    def test_duplicate_message_id_is_rejected_as_replay(self):
        message = self.make_message()
        self.service.verify_and_accept(message, self.workspace, self.recipient)
        with self.assertRaisesRegex(ValueError, "message_replay_detected"):
            self.service.verify_and_accept(message, self.workspace, self.recipient)

    def test_expired_message_is_rejected(self):
        message = self.service.create_message(
            self.workspace, self.sender, self.key_id, self.recipient,
            "entity.notice", {"text": "old"}, self.private, ttl_seconds=1
        )
        from datetime import datetime, timedelta, timezone
        expired = (datetime.now(timezone.utc) - timedelta(seconds=5)).isoformat()
        message["issued_at"] = expired
        message["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        message.pop("signature")
        from xparallel.entity_messaging import message_signing_bytes
        message["signature"] = base64.b64encode(
            self.private.sign(message_signing_bytes(message))
        ).decode("ascii")
        with self.assertRaisesRegex(ValueError, "message_expired"):
            self.service.verify_and_accept(message, self.workspace, self.recipient)

    def test_revoked_sender_key_cannot_send_or_verify(self):
        message = self.make_message()
        key = self.key_store.get_key(self.workspace, self.sender, self.key_id)
        # Revoke with a configured authority is covered by identity trust tests;
        # rotate the sender key here to establish an inactive signing key state.
        new_private = Ed25519PrivateKey.generate()
        new_id = "sender-key-2"
        self.key_store.register_pending_key(
            self.workspace, self.sender, new_id, public_b64(new_private)
        )
        challenge = self.key_store.create_owner_challenge(self.workspace, self.sender, new_id)
        rotation = __import__("xparallel.identity_trust", fromlist=["rotation_message"]).rotation_message(
            self.workspace, self.sender, self.key_id, new_id,
            public_b64(new_private), challenge["challenge_id"]
        )
        old_sig = base64.b64encode(self.private.sign(rotation)).decode("ascii")
        new_sig = base64.b64encode(
            new_private.sign(base64.b64decode(challenge["message_b64"]))
        ).decode("ascii")
        self.key_store.rotate_key(
            self.workspace, self.sender, self.key_id, new_id,
            public_b64(new_private), challenge["challenge_id"], old_sig, new_sig
        )
        with self.assertRaisesRegex(ValueError, "sender_key_not_active"):
            self.service.verify_and_accept(message, self.workspace, self.recipient)
        with self.assertRaisesRegex(ValueError, "sender_key_not_active"):
            self.service.create_message(
                self.workspace, self.sender, self.key_id, self.recipient,
                "entity.notice", {"text": "no"}, self.private
            )

    def test_malformed_envelope_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_message_envelope"):
            self.service.verify_and_accept([], self.workspace, self.recipient)

    def test_private_key_material_is_not_returned_or_stored(self):
        message = self.make_message()
        self.assertNotIn("private_key", message)
        self.assertNotIn("private_key", str(self.key_store.get_key(
            self.workspace, self.sender, self.key_id
        )).lower())


if __name__ == "__main__":
    unittest.main()
