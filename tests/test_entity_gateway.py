import base64
import tempfile
import unittest
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from xparallel.entity_gateway import EntityCommunicationGateway
from xparallel.entity_messaging import EntityMessageService
from xparallel.identity_trust import EntityKeyStore


def public_b64(private_key):
    raw = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return base64.b64encode(raw).decode("ascii")


class EntityGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.keys = EntityKeyStore(str(root / "keys.sqlite3"))
        self.messages = EntityMessageService(self.keys, str(root / "messages.sqlite3"))
        self.private = Ed25519PrivateKey.generate()
        self.keys.register_pending_key("ws-a", "entity-a", "key-a", public_b64(self.private))
        challenge = self.keys.create_owner_challenge("ws-a", "entity-a", "key-a")
        signature = base64.b64encode(self.private.sign(base64.b64decode(challenge["message_b64"]))).decode("ascii")
        self.keys.verify_owner_challenge("ws-a", "entity-a", "key-a", challenge["challenge_id"], signature)
        self.sessions = {
            "sender-session": {"authenticated": True, "workspace_id": "ws-a", "entity_id": "entity-a", "subject": "owner-a"},
            "recipient-session": {"authenticated": True, "workspace_id": "ws-a", "entity_id": "entity-b", "subject": "owner-b"},
            "outsider-session": {"authenticated": True, "workspace_id": "ws-a", "entity_id": "entity-c", "subject": "owner-c"},
            "other-workspace": {"authenticated": True, "workspace_id": "ws-b", "entity_id": "entity-b", "subject": "owner-b"},
            "unauthenticated": {"authenticated": False},
        }
        self.denied = set()
        def authenticate(session):
            return self.sessions.get(session, {"authenticated": False})
        def authorize(identity, metadata, direction):
            key = (identity["entity_id"], direction, metadata.get("recipient_entity_id"), metadata.get("sender_entity_id"))
            return {"allowed": key not in self.denied, "reason": "test_policy_denied"}
        self.gateway = EntityCommunicationGateway(
            self.messages, authenticate=authenticate, authorize=authorize,
            db_path=str(root / "gateway.sqlite3")
        )

    def tearDown(self):
        self.gateway.close()
        self.messages.close()
        self.keys.close()
        self.temp.cleanup()

    def message(self):
        return self.messages.create_message(
            "ws-a", "entity-a", "key-a", "entity-b",
            "entity.notice", {"message": "hello"}, self.private
        )

    def test_send_then_authorized_recipient_pull(self):
        envelope = self.message()
        queued = self.gateway.submit("sender-session", envelope)
        self.assertTrue(queued["queued"])
        inbox = self.gateway.receive("recipient-session")
        self.assertEqual(inbox["count"], 1)
        self.assertEqual(inbox["messages"][0]["body"]["message"], "hello")
        self.assertEqual(self.gateway.status("sender-session", envelope["message_id"])["delivered_at"] is not None, True)

    def test_unauthenticated_sender_rejected(self):
        with self.assertRaisesRegex(PermissionError, "caller_not_authenticated"):
            self.gateway.submit("unauthenticated", self.message())

    def test_sender_identity_must_match_signed_envelope(self):
        with self.assertRaisesRegex(PermissionError, "authenticated_sender_mismatch"):
            self.gateway.submit("recipient-session", self.message())

    def test_send_requires_explicit_authorization(self):
        self.denied.add(("entity-a", "send", "entity-b", "entity-a"))
        with self.assertRaisesRegex(PermissionError, "test_policy_denied"):
            self.gateway.submit("sender-session", self.message())

    def test_receive_requires_explicit_authorization(self):
        envelope = self.message()
        self.gateway.submit("sender-session", envelope)
        self.denied.add(("entity-b", "receive", "entity-b", "entity-a"))
        self.assertEqual(self.gateway.receive("recipient-session")["count"], 0)
        self.assertIsNone(self.gateway.status("sender-session", envelope["message_id"])["delivered_at"])

    def test_workspace_isolation(self):
        with self.assertRaisesRegex(PermissionError, "message_workspace_mismatch"):
            self.gateway.submit("other-workspace", self.message())
        self.gateway.submit("sender-session", self.message())
        self.assertEqual(self.gateway.receive("other-workspace")["count"], 0)

    def test_outsider_cannot_read_message_status(self):
        envelope = self.message()
        self.gateway.submit("sender-session", envelope)
        with self.assertRaisesRegex(PermissionError, "message_status_forbidden"):
            self.gateway.status("outsider-session", envelope["message_id"])

    def test_message_replay_is_rejected(self):
        envelope = self.message()
        self.gateway.submit("sender-session", envelope)
        with self.assertRaisesRegex(ValueError, "message_replay_detected"):
            self.gateway.submit("sender-session", envelope)

    def test_duplicate_queue_entry_is_not_created(self):
        envelope = self.message()
        self.gateway.submit("sender-session", envelope)
        self.assertEqual(self.gateway.receive("recipient-session")["count"], 1)
        self.assertEqual(self.gateway.receive("recipient-session")["count"], 0)

    def test_audit_records_queue_and_delivery(self):
        envelope = self.message()
        self.gateway.submit("sender-session", envelope)
        self.gateway.receive("recipient-session")
        events = self.gateway.audit_events("sender-session", envelope["message_id"])
        self.assertEqual([e["event_type"] for e in events], ["queued", "delivered"])

    def test_expired_queued_message_is_not_delivered(self):
        import time
        envelope = self.messages.create_message(
            "ws-a", "entity-a", "key-a", "entity-b",
            "entity.notice", {"message": "expires"}, self.private, ttl_seconds=1
        )
        self.gateway.submit("sender-session", envelope)
        time.sleep(1.1)
        self.assertEqual(self.gateway.receive("recipient-session")["count"], 0)
        self.assertEqual(self.gateway.status("sender-session", envelope["message_id"])["expired_at"] is not None, True)
        events = self.gateway.audit_events("sender-session", envelope["message_id"])
        self.assertEqual([event["event_type"] for event in events], ["queued", "expired"])

    def test_outsider_cannot_read_message_audit(self):
        envelope = self.message()
        self.gateway.submit("sender-session", envelope)
        with self.assertRaisesRegex(PermissionError, "message_audit_forbidden"):
            self.gateway.audit_events("outsider-session", envelope["message_id"])

    def test_injected_authorization_adapter_is_mandatory(self):
        with self.assertRaises(TypeError):
            EntityCommunicationGateway(self.messages, authenticate=lambda s: {}, authorize=None)


if __name__ == "__main__":
    unittest.main()
