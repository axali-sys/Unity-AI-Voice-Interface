"""Ed25519 key proof and lifecycle primitives for XParallel Digital DNA.

This module proves possession of registered keys. It does not establish a legal
identity, authenticate a workspace session, certify capabilities, or authorize
runtime actions. Those must be enforced by separate trusted services.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

try:
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError as exc:  # pragma: no cover - exercised in dependency-missing environments
    raise RuntimeError(
        "Ed25519 support requires the open-source 'cryptography' package"
    ) from exc


_LOCK = threading.RLock()
KEY_STATUSES = {"pending", "active", "rotated", "revoked"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _b64decode(value: str, name: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid_{name}")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"invalid_{name}") from exc


def _public_key(value: str) -> Ed25519PublicKey:
    raw = _b64decode(value, "public_key")
    if len(raw) != 32:
        raise ValueError("ed25519_public_key_must_be_32_bytes")
    try:
        return Ed25519PublicKey.from_public_bytes(raw)
    except ValueError as exc:
        raise ValueError("invalid_ed25519_public_key") from exc


def _verify(public_key: Ed25519PublicKey, message: bytes, signature_b64: str) -> None:
    signature = _b64decode(signature_b64, "signature")
    try:
        public_key.verify(signature, message)
    except InvalidSignature as exc:
        raise ValueError("signature_verification_failed") from exc


def _canonical(value: dict[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def owner_challenge_message(workspace_id: str, entity_id: str, key_id: str,
                            challenge_id: str, nonce: str, expires_at: str) -> bytes:
    """Return the exact domain-separated bytes a key holder must sign."""
    return b"XPARALLEL-OWNER-PROOF-V1\n" + _canonical({
        "workspace_id": workspace_id, "entity_id": entity_id, "key_id": key_id,
        "challenge_id": challenge_id, "nonce": nonce, "expires_at": expires_at,
    })


def rotation_message(workspace_id: str, entity_id: str, old_key_id: str,
                     new_key_id: str, new_public_key_b64: str,
                     challenge_id: str) -> bytes:
    return b"XPARALLEL-KEY-ROTATION-V1\n" + _canonical({
        "workspace_id": workspace_id, "entity_id": entity_id,
        "old_key_id": old_key_id, "new_key_id": new_key_id,
        "new_public_key_sha256": hashlib.sha256(
            _b64decode(new_public_key_b64, "public_key")
        ).hexdigest(),
        "challenge_id": challenge_id,
    })


def revocation_message(workspace_id: str, entity_id: str, key_id: str,
                       reason: str, issued_at: str) -> bytes:
    return b"XPARALLEL-KEY-REVOCATION-V1\n" + _canonical({
        "workspace_id": workspace_id, "entity_id": entity_id, "key_id": key_id,
        "reason": reason, "issued_at": issued_at,
    })


class EntityKeyStore:
    """SQLite key registry. Private keys are never accepted or stored here."""

    def __init__(self, db_path: str = ".xparallel/entity_keys.sqlite3",
                 authority_public_key_b64: str | None = None):
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._authority_key = _public_key(authority_public_key_b64) if authority_public_key_b64 else None
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS entity_keys (
                workspace_id TEXT NOT NULL, entity_id TEXT NOT NULL, key_id TEXT NOT NULL,
                public_key_b64 TEXT NOT NULL, fingerprint TEXT NOT NULL,
                status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY (workspace_id, entity_id, key_id),
                UNIQUE (workspace_id, entity_id, fingerprint)
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS owner_challenges (
                workspace_id TEXT NOT NULL, entity_id TEXT NOT NULL, key_id TEXT NOT NULL,
                challenge_id TEXT NOT NULL, nonce TEXT NOT NULL, expires_at TEXT NOT NULL,
                consumed_at TEXT, created_at TEXT NOT NULL,
                PRIMARY KEY (workspace_id, entity_id, challenge_id)
            )
        """)
        self._db.commit()

    @staticmethod
    def _scope(workspace_id: str, entity_id: str, key_id: str) -> tuple[str, str, str]:
        values = tuple(str(v or "").strip() for v in (workspace_id, entity_id, key_id))
        if any(not v or len(v) > 200 for v in values):
            raise ValueError("invalid_key_scope")
        return values

    def register_pending_key(self, workspace_id: str, entity_id: str,
                             key_id: str, public_key_b64: str) -> dict[str, Any]:
        workspace, entity, key = self._scope(workspace_id, entity_id, key_id)
        raw = _b64decode(public_key_b64, "public_key")
        _public_key(public_key_b64)
        fingerprint = hashlib.sha256(raw).hexdigest()
        now = _iso(_utcnow())
        with _LOCK, self._db:
            if self._db.execute(
                "SELECT 1 FROM entity_keys WHERE workspace_id=? AND entity_id=? AND key_id=?",
                (workspace, entity, key),
            ).fetchone():
                raise ValueError("key_id_already_registered")
            try:
                self._db.execute(
                    """INSERT INTO entity_keys VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)""",
                    (workspace, entity, key, public_key_b64, fingerprint, now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("public_key_already_registered") from exc
        return {"workspace_id": workspace, "entity_id": entity, "key_id": key,
                "fingerprint_sha256": fingerprint, "status": "pending"}

    def create_owner_challenge(self, workspace_id: str, entity_id: str, key_id: str,
                               ttl_seconds: int = 300) -> dict[str, str]:
        workspace, entity, key = self._scope(workspace_id, entity_id, key_id)
        if not isinstance(ttl_seconds, int) or not 30 <= ttl_seconds <= 900:
            raise ValueError("challenge_ttl_out_of_range")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT status FROM entity_keys WHERE workspace_id=? AND entity_id=? AND key_id=?",
                (workspace, entity, key),
            ).fetchone()
            if row is None:
                raise ValueError("key_not_found")
            if row["status"] != "pending":
                raise ValueError("challenge_requires_pending_key")
            challenge_id = secrets.token_urlsafe(18)
            nonce = secrets.token_urlsafe(32)
            expires = _iso(_utcnow() + timedelta(seconds=ttl_seconds))
            created = _iso(_utcnow())
            self._db.execute(
                """INSERT INTO owner_challenges
                   (workspace_id, entity_id, key_id, challenge_id, nonce, expires_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (workspace, entity, key, challenge_id, nonce, expires, created),
            )
        message = owner_challenge_message(workspace, entity, key, challenge_id, nonce, expires)
        return {"challenge_id": challenge_id, "nonce": nonce, "expires_at": expires,
                "message_b64": base64.b64encode(message).decode("ascii")}

    def verify_owner_challenge(self, workspace_id: str, entity_id: str, key_id: str,
                               challenge_id: str, signature_b64: str) -> dict[str, str]:
        workspace, entity, key = self._scope(workspace_id, entity_id, key_id)
        with _LOCK, self._db:
            row = self._db.execute(
                """SELECT * FROM owner_challenges WHERE workspace_id=? AND entity_id=?
                   AND key_id=? AND challenge_id=?""",
                (workspace, entity, key, challenge_id),
            ).fetchone()
            if row is None:
                raise ValueError("challenge_not_found")
            if row["consumed_at"] is not None:
                raise ValueError("challenge_already_used")
            if _utcnow() >= datetime.fromisoformat(row["expires_at"]):
                raise ValueError("challenge_expired")
            key_row = self._db.execute(
                """SELECT * FROM entity_keys WHERE workspace_id=? AND entity_id=? AND key_id=?""",
                (workspace, entity, key),
            ).fetchone()
            if key_row is None or key_row["status"] != "pending":
                raise ValueError("key_not_pending")
            message = owner_challenge_message(
                workspace, entity, key, challenge_id, row["nonce"], row["expires_at"]
            )
            _verify(_public_key(key_row["public_key_b64"]), message, signature_b64)
            now = _iso(_utcnow())
            self._db.execute(
                """UPDATE owner_challenges SET consumed_at=? WHERE workspace_id=?
                   AND entity_id=? AND challenge_id=? AND consumed_at IS NULL""",
                (now, workspace, entity, challenge_id),
            )
            self._db.execute(
                """UPDATE entity_keys SET status='active', updated_at=?
                   WHERE workspace_id=? AND entity_id=? AND key_id=? AND status='pending'""",
                (now, workspace, entity, key),
            )
        return {"key_id": key, "status": "active", "proof": "verified"}

    def rotate_key(self, workspace_id: str, entity_id: str, old_key_id: str,
                   new_key_id: str, new_public_key_b64: str, challenge_id: str,
                   old_key_signature_b64: str, new_key_proof_signature_b64: str) -> dict[str, str]:
        workspace, entity, old_key = self._scope(workspace_id, entity_id, old_key_id)
        _, _, new_key = self._scope(workspace_id, entity_id, new_key_id)
        if old_key == new_key:
            raise ValueError("rotation_requires_new_key_id")
        raw = _b64decode(new_public_key_b64, "public_key")
        _public_key(new_public_key_b64)
        fingerprint = hashlib.sha256(raw).hexdigest()
        with _LOCK, self._db:
            old = self._db.execute(
                "SELECT * FROM entity_keys WHERE workspace_id=? AND entity_id=? AND key_id=?",
                (workspace, entity, old_key),
            ).fetchone()
            new = self._db.execute(
                "SELECT * FROM entity_keys WHERE workspace_id=? AND entity_id=? AND key_id=?",
                (workspace, entity, new_key),
            ).fetchone()
            challenge = self._db.execute(
                """SELECT * FROM owner_challenges WHERE workspace_id=? AND entity_id=?
                   AND key_id=? AND challenge_id=?""",
                (workspace, entity, new_key, challenge_id),
            ).fetchone()
            if old is None or old["status"] != "active":
                raise ValueError("old_key_not_active")
            if new is None or new["status"] != "pending" or new["fingerprint"] != fingerprint:
                raise ValueError("new_key_not_pending_or_mismatched")
            if challenge is None or challenge["consumed_at"] is not None:
                raise ValueError("new_key_challenge_invalid_or_used")
            if _utcnow() >= datetime.fromisoformat(challenge["expires_at"]):
                raise ValueError("challenge_expired")
            rotation = rotation_message(workspace, entity, old_key, new_key,
                                        new_public_key_b64, challenge_id)
            _verify(_public_key(old["public_key_b64"]), rotation, old_key_signature_b64)
            proof = owner_challenge_message(workspace, entity, new_key, challenge_id,
                                            challenge["nonce"], challenge["expires_at"])
            _verify(_public_key(new["public_key_b64"]), proof, new_key_proof_signature_b64)
            now = _iso(_utcnow())
            self._db.execute(
                """UPDATE entity_keys SET status='rotated', updated_at=?
                   WHERE workspace_id=? AND entity_id=? AND key_id=?""",
                (now, workspace, entity, old_key),
            )
            self._db.execute(
                """UPDATE entity_keys SET status='active', updated_at=?
                   WHERE workspace_id=? AND entity_id=? AND key_id=?""",
                (now, workspace, entity, new_key),
            )
            self._db.execute(
                """UPDATE owner_challenges SET consumed_at=? WHERE workspace_id=?
                   AND entity_id=? AND challenge_id=?""",
                (now, workspace, entity, challenge_id),
            )
        return {"old_key_id": old_key, "old_status": "rotated",
                "new_key_id": new_key, "new_status": "active"}

    def revoke_key(self, workspace_id: str, entity_id: str, key_id: str,
                   reason: str, issued_at: str, authority_signature_b64: str) -> dict[str, str]:
        workspace, entity, key = self._scope(workspace_id, entity_id, key_id)
        if self._authority_key is None:
            raise ValueError("revocation_authority_not_configured")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 300:
            raise ValueError("invalid_revocation_reason")
        try:
            issued = datetime.fromisoformat(issued_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as exc:
            raise ValueError("invalid_revocation_timestamp") from exc
        if abs((_utcnow() - issued.astimezone(timezone.utc)).total_seconds()) > 300:
            raise ValueError("revocation_statement_outside_time_window")
        _verify(self._authority_key, revocation_message(
            workspace, entity, key, reason.strip(), issued_at
        ), authority_signature_b64)
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT status FROM entity_keys WHERE workspace_id=? AND entity_id=? AND key_id=?",
                (workspace, entity, key),
            ).fetchone()
            if row is None:
                raise ValueError("key_not_found")
            if row["status"] in {"revoked", "rotated"}:
                raise ValueError("key_already_inactive")
            self._db.execute(
                """UPDATE entity_keys SET status='revoked', updated_at=?
                   WHERE workspace_id=? AND entity_id=? AND key_id=?""",
                (_iso(_utcnow()), workspace, entity, key),
            )
        return {"key_id": key, "status": "revoked", "reason": reason.strip()}

    def get_key(self, workspace_id: str, entity_id: str, key_id: str) -> dict[str, Any] | None:
        workspace, entity, key = self._scope(workspace_id, entity_id, key_id)
        with _LOCK:
            row = self._db.execute(
                """SELECT workspace_id, entity_id, key_id, public_key_b64, fingerprint,
                   status, created_at, updated_at FROM entity_keys
                   WHERE workspace_id=? AND entity_id=? AND key_id=?""",
                (workspace, entity, key),
            ).fetchone()
        return dict(row) if row else None

    def close(self) -> None:
        with _LOCK:
            self._db.close()
