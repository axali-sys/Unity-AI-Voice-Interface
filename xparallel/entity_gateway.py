"""Policy-gated local XParallel message routing gateway.

This is a pull-based local prototype. Authentication and authorization are
mandatory injected trusted adapters; this module does not infer identity from
request bodies, bearer tokens, or message signatures.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from xparallel.entity_messaging import EntityMessageService, _identifier

_GATEWAY_LOCK = threading.RLock()
_MAX_INBOX = 100


class EntityCommunicationGateway:
    """Validate, authorize, queue, and pull-deliver signed entity messages.

    authenticate(session) -> trusted identity dict
    authorize(identity, message_metadata, direction) -> {"allowed": bool, ...}

    Identity must include authenticated=True, workspace_id, entity_id and
    subject. The authorize callback must apply the application's explicit
    entity action grants; this gateway deliberately has no permissive default.
    """

    def __init__(
        self,
        message_service: EntityMessageService,
        *,
        authenticate: Callable[[Any], dict[str, Any]],
        authorize: Callable[[dict[str, Any], dict[str, Any], str], dict[str, Any]],
        db_path: str = ".xparallel/entity_gateway.sqlite3",
    ):
        if not isinstance(message_service, EntityMessageService):
            raise TypeError("trusted_message_service_required")
        if not callable(authenticate) or not callable(authorize):
            raise TypeError("trusted_authentication_and_authorization_adapters_required")
        self._messages = message_service
        self._authenticate = authenticate
        self._authorize_callback = authorize
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS entity_gateway_queue (
                workspace_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                sender_entity_id TEXT NOT NULL,
                recipient_entity_id TEXT NOT NULL,
                envelope_json TEXT NOT NULL,
                queued_at TEXT NOT NULL,
                delivered_at TEXT,
                expired_at TEXT,
                PRIMARY KEY (workspace_id, message_id)
            )
        """)
        columns = {row[1] for row in self._db.execute("PRAGMA table_info(entity_gateway_queue)").fetchall()}
        if "expired_at" not in columns:
            self._db.execute("ALTER TABLE entity_gateway_queue ADD COLUMN expired_at TEXT")
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS entity_gateway_inbox
            ON entity_gateway_queue(workspace_id, recipient_entity_id, delivered_at, queued_at)
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS entity_gateway_audit (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL,
                message_id TEXT NOT NULL,
                actor_entity_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                detail_json TEXT NOT NULL
            )
        """)
        self._db.commit()

    def _identity(self, session: Any) -> dict[str, Any]:
        identity = self._authenticate(session)
        if not isinstance(identity, dict) or identity.get("authenticated") is not True:
            raise PermissionError("caller_not_authenticated")
        for field in ("workspace_id", "entity_id", "subject"):
            value = identity.get(field)
            if not isinstance(value, str) or not value.strip():
                raise PermissionError("trusted_identity_context_incomplete")
        _identifier(identity["workspace_id"], "workspace_id")
        _identifier(identity["entity_id"], "entity_id")
        return identity

    def _require_authorized(self, identity: dict[str, Any], metadata: dict[str, Any], direction: str) -> None:
        decision = self._authorize_callback(identity, metadata, direction)
        if not isinstance(decision, dict) or decision.get("allowed") is not True:
            reason = decision.get("reason", "authorization_denied") if isinstance(decision, dict) else "authorization_denied"
            raise PermissionError(str(reason))

    def submit(self, session: Any, envelope: dict[str, Any]) -> dict[str, Any]:
        identity = self._identity(session)
        if not isinstance(envelope, dict):
            raise ValueError("invalid_message_envelope")
        workspace = envelope.get("workspace_id")
        sender = envelope.get("sender_entity_id")
        recipient = envelope.get("recipient_entity_id")
        message_id = envelope.get("message_id")
        if identity["workspace_id"] != workspace:
            raise PermissionError("message_workspace_mismatch")
        if identity["entity_id"] != sender:
            raise PermissionError("authenticated_sender_mismatch")
        metadata = {
            "workspace_id": workspace, "message_id": message_id,
            "sender_entity_id": sender, "recipient_entity_id": recipient,
            "message_type": envelope.get("message_type"),
        }
        self._require_authorized(identity, metadata, "send")
        verified = self._messages.verify_and_accept(
            envelope, expected_workspace_id=identity["workspace_id"],
            expected_recipient_entity_id=recipient,
        )
        now = datetime.now(timezone.utc).isoformat()
        encoded = json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with _GATEWAY_LOCK, self._db:
            try:
                self._db.execute(
                    """INSERT INTO entity_gateway_queue
                       (workspace_id, message_id, sender_entity_id, recipient_entity_id,
                        envelope_json, queued_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (workspace, message_id, sender, recipient, encoded, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ValueError("gateway_duplicate_message") from exc
            self._audit(workspace, message_id, sender, "queued", {"message_type": metadata["message_type"]}, now)
        return {"queued": True, "message_id": verified["message_id"], "recipient_entity_id": recipient, "queued_at": now}

    def receive(self, session: Any, limit: int = 20) -> dict[str, Any]:
        identity = self._identity(session)
        if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_INBOX:
            raise ValueError("invalid_inbox_limit")
        workspace, recipient = identity["workspace_id"], identity["entity_id"]
        with _GATEWAY_LOCK:
            rows = self._db.execute(
                """SELECT * FROM entity_gateway_queue
                   WHERE workspace_id=? AND recipient_entity_id=? AND delivered_at IS NULL AND expired_at IS NULL
                   ORDER BY queued_at, message_id LIMIT ?""",
                (workspace, recipient, limit),
            ).fetchall()
        delivered = []
        for row in rows:
            envelope = json.loads(row["envelope_json"])
            expires_at = datetime.fromisoformat(envelope["expires_at"].replace("Z", "+00:00"))
            if expires_at.tzinfo is None or expires_at <= datetime.now(timezone.utc):
                expired_at = datetime.now(timezone.utc).isoformat()
                with _GATEWAY_LOCK, self._db:
                    cursor = self._db.execute(
                        """UPDATE entity_gateway_queue SET expired_at=?
                           WHERE workspace_id=? AND message_id=? AND delivered_at IS NULL AND expired_at IS NULL""",
                        (expired_at, workspace, row["message_id"]),
                    )
                    if cursor.rowcount == 1:
                        self._audit(workspace, row["message_id"], recipient, "expired", {}, expired_at)
                continue
            metadata = {
                "workspace_id": workspace, "message_id": row["message_id"],
                "sender_entity_id": row["sender_entity_id"],
                "recipient_entity_id": recipient,
                "message_type": envelope.get("message_type"),
            }
            try:
                self._require_authorized(identity, metadata, "receive")
            except PermissionError:
                continue
            now = datetime.now(timezone.utc).isoformat()
            with _GATEWAY_LOCK, self._db:
                cursor = self._db.execute(
                    """UPDATE entity_gateway_queue SET delivered_at=?
                       WHERE workspace_id=? AND message_id=? AND delivered_at IS NULL""",
                    (now, workspace, row["message_id"]),
                )
                if cursor.rowcount != 1:
                    continue
                self._audit(workspace, row["message_id"], recipient, "delivered", {"sender_entity_id": row["sender_entity_id"]}, now)
            delivered.append({
                "message_id": row["message_id"],
                "sender_entity_id": row["sender_entity_id"],
                "recipient_entity_id": recipient,
                "message_type": envelope["message_type"],
                "body": envelope["body"],
                "queued_at": row["queued_at"],
                "delivered_at": now,
            })
        return {"workspace_id": workspace, "entity_id": recipient, "messages": delivered, "count": len(delivered)}

    def status(self, session: Any, message_id: str) -> dict[str, Any] | None:
        identity = self._identity(session)
        _identifier(message_id, "message_id")
        with _GATEWAY_LOCK:
            row = self._db.execute(
                """SELECT message_id, sender_entity_id, recipient_entity_id,
                          queued_at, delivered_at, expired_at
                   FROM entity_gateway_queue
                   WHERE workspace_id=? AND message_id=?""",
                (identity["workspace_id"], message_id),
            ).fetchone()
        if row is None:
            return None
        if identity["entity_id"] not in (row["sender_entity_id"], row["recipient_entity_id"]):
            raise PermissionError("message_status_forbidden")
        return dict(row)

    def _audit(self, workspace: str, message_id: str, actor: str,
               event_type: str, detail: dict[str, Any], occurred_at: str) -> None:
        self._db.execute(
            """INSERT INTO entity_gateway_audit
               (workspace_id, message_id, actor_entity_id, event_type, occurred_at, detail_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (workspace, message_id, actor, event_type, occurred_at,
             json.dumps(detail, sort_keys=True, separators=(",", ":"))),
        )

    def audit_events(self, session: Any, message_id: str) -> list[dict[str, Any]]:
        identity = self._identity(session)
        _identifier(message_id, "message_id")
        with _GATEWAY_LOCK:
            owner = self._db.execute(
                """SELECT sender_entity_id, recipient_entity_id
                   FROM entity_gateway_queue WHERE workspace_id=? AND message_id=?""",
                (identity["workspace_id"], message_id),
            ).fetchone()
            if owner is None:
                return []
            if identity["entity_id"] not in (owner["sender_entity_id"], owner["recipient_entity_id"]):
                raise PermissionError("message_audit_forbidden")
            rows = self._db.execute(
                """SELECT actor_entity_id, event_type, occurred_at, detail_json
                   FROM entity_gateway_audit WHERE workspace_id=? AND message_id=?
                   ORDER BY event_id""",
                (identity["workspace_id"], message_id),
            ).fetchall()
        return [{
            "actor_entity_id": row["actor_entity_id"],
            "event_type": row["event_type"],
            "occurred_at": row["occurred_at"],
            "detail": json.loads(row["detail_json"]),
        } for row in rows]

    def close(self) -> None:
        with _GATEWAY_LOCK:
            self._db.close()
