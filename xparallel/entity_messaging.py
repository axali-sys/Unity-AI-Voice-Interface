"""Signed, replay-resistant XParallel entity message envelopes.

This is a local protocol primitive, not a transport or delivery service. It relies
on a trusted EntityKeyStore for active sender-key status and on callers to supply
the recipient identity expected by the receiving endpoint.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from xparallel.identity_trust import EntityKeyStore

_LOCK = threading.RLock()
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_TYPE_RE = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_DOMAIN = b"XPARALLEL-ENTITY-MESSAGE-V1\n"
_MAX_BODY_BYTES = 256_000


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _parse_time(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid_{field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"invalid_{field}")
    return parsed.astimezone(timezone.utc)


def _identifier(value: str, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _b64(value: str, field: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid_{field}")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def message_signing_bytes(envelope: dict[str, Any]) -> bytes:
    """Return canonical, domain-separated bytes excluding the signature."""
    unsigned = {key: value for key, value in envelope.items() if key != "signature"}
    return _DOMAIN + _canonical(unsigned)


class EntityMessageService:
    """Create and verify envelopes; persist accepted IDs to reject replay."""

    def __init__(self, key_store: EntityKeyStore,
                 db_path: str = ".xparallel/entity_messages.sqlite3"):
        if not isinstance(key_store, EntityKeyStore):
            raise TypeError("trusted_entity_key_store_required")
        self._keys = key_store
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS accepted_entity_messages (
                workspace_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                sender_entity_id TEXT NOT NULL,
                recipient_entity_id TEXT NOT NULL,
                accepted_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                PRIMARY KEY (workspace_id, message_id)
            )
        """)
        self._db.commit()

    def create_message(self, workspace_id: str, sender_entity_id: str,
                       sender_key_id: str, recipient_entity_id: str,
                       message_type: str, body: Any, private_key: Any,
                       ttl_seconds: int = 300) -> dict[str, Any]:
        workspace = _identifier(workspace_id, "workspace_id")
        sender = _identifier(sender_entity_id, "sender_entity_id")
        key_id = _identifier(sender_key_id, "sender_key_id")
        recipient = _identifier(recipient_entity_id, "recipient_entity_id")
        if not isinstance(message_type, str) or not _TYPE_RE.fullmatch(message_type):
            raise ValueError("invalid_message_type")
        if not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 86400:
            raise ValueError("message_ttl_out_of_range")
        key = self._keys.get_key(workspace, sender, key_id)
        if key is None or key["status"] != "active":
            raise ValueError("sender_key_not_active")
        if not hasattr(private_key, "sign"):
            raise ValueError("ed25519_private_key_required")
        try:
            encoded_body = _canonical({"body": body})
        except (TypeError, ValueError) as exc:
            raise ValueError("body_must_be_json_serializable") from exc
        if len(encoded_body) > _MAX_BODY_BYTES:
            raise ValueError("message_body_too_large")
        now = _now()
        envelope = {
            "schema_version": "1.0",
            "message_id": secrets.token_urlsafe(24),
            "workspace_id": workspace,
            "sender_entity_id": sender,
            "sender_key_id": key_id,
            "recipient_entity_id": recipient,
            "message_type": message_type,
            "issued_at": _iso(now),
            "expires_at": _iso(now + timedelta(seconds=ttl_seconds)),
            "body": body,
            "body_sha256": hashlib.sha256(encoded_body).hexdigest(),
        }
        envelope["signature"] = base64.b64encode(
            private_key.sign(message_signing_bytes(envelope))
        ).decode("ascii")
        return envelope

    def verify_and_accept(self, envelope: dict[str, Any], expected_workspace_id: str,
                          expected_recipient_entity_id: str,
                          clock_skew_seconds: int = 60) -> dict[str, Any]:
        if not isinstance(envelope, dict):
            raise ValueError("invalid_message_envelope")
        required = {
            "schema_version", "message_id", "workspace_id", "sender_entity_id",
            "sender_key_id", "recipient_entity_id", "message_type", "issued_at",
            "expires_at", "body", "body_sha256", "signature",
        }
        if set(envelope) != required:
            raise ValueError("invalid_message_envelope_fields")
        if envelope["schema_version"] != "1.0":
            raise ValueError("unsupported_message_schema")
        workspace = _identifier(envelope["workspace_id"], "workspace_id")
        message_id = _identifier(envelope["message_id"], "message_id")
        sender = _identifier(envelope["sender_entity_id"], "sender_entity_id")
        key_id = _identifier(envelope["sender_key_id"], "sender_key_id")
        recipient = _identifier(envelope["recipient_entity_id"], "recipient_entity_id")
        expected_workspace = _identifier(expected_workspace_id, "expected_workspace_id")
        expected_recipient = _identifier(expected_recipient_entity_id, "expected_recipient_entity_id")
        if workspace != expected_workspace:
            raise ValueError("message_workspace_mismatch")
        if recipient != expected_recipient:
            raise ValueError("message_recipient_mismatch")
        if not isinstance(envelope["message_type"], str) or not _TYPE_RE.fullmatch(envelope["message_type"]):
            raise ValueError("invalid_message_type")
        if not isinstance(envelope["body_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", envelope["body_sha256"]):
            raise ValueError("invalid_body_digest")
        try:
            body_bytes = _canonical({"body": envelope["body"]})
        except (TypeError, ValueError) as exc:
            raise ValueError("invalid_message_body") from exc
        if len(body_bytes) > _MAX_BODY_BYTES:
            raise ValueError("message_body_too_large")
        if hashlib.sha256(body_bytes).hexdigest() != envelope["body_sha256"]:
            raise ValueError("message_body_digest_mismatch")
        issued = _parse_time(envelope["issued_at"], "issued_at")
        expires = _parse_time(envelope["expires_at"], "expires_at")
        now = _now()
        if expires <= issued or expires - issued > timedelta(days=1):
            raise ValueError("invalid_message_lifetime")
        if issued > now + timedelta(seconds=clock_skew_seconds):
            raise ValueError("message_issued_in_future")
        if now >= expires:
            raise ValueError("message_expired")
        key = self._keys.get_key(workspace, sender, key_id)
        if key is None or key["status"] != "active":
            raise ValueError("sender_key_not_active")
        try:
            signature = _b64(envelope["signature"], "signature")
            public_raw = _b64(key["public_key_b64"], "public_key")
            Ed25519PublicKey.from_public_bytes(public_raw).verify(
                signature, message_signing_bytes(envelope)
            )
        except InvalidSignature as exc:
            raise ValueError("message_signature_invalid") from exc
        except (ValueError, TypeError) as exc:
            if str(exc).startswith("invalid_"):
                raise
            raise ValueError("message_signature_invalid") from exc
        with _LOCK, self._db:
            try:
                self._db.execute(
                    """INSERT INTO accepted_entity_messages
                       (workspace_id, message_id, sender_entity_id, recipient_entity_id,
                        accepted_at, expires_at) VALUES (?, ?, ?, ?, ?, ?)""",
                    (workspace, message_id, sender, recipient, _iso(now), _iso(expires)),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("message_replay_detected") from exc
        return {
            "accepted": True, "message_id": message_id,
            "sender_entity_id": sender, "recipient_entity_id": recipient,
            "message_type": envelope["message_type"], "body": envelope["body"],
            "accepted_at": _iso(now),
        }

    def close(self) -> None:
        with _LOCK:
            self._db.close()
