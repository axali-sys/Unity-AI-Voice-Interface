"""Persistent, deny-by-default governance registry for XParallel entity grants.

All principals, ownership, and governance authority are supplied by trusted
server-side adapters. This module never trusts caller-provided role or owner
claims and does not itself authenticate HTTP requests.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

_LOCK = threading.RLock()
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_MAX_TTL_SECONDS = 90 * 24 * 60 * 60
_MAX_SCOPE_LENGTH = 500


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _valid_id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


def _principal(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("authenticated") is not True:
        raise PermissionError("caller_not_authenticated")
    subject = value.get("subject")
    workspace = value.get("workspace_id")
    if not isinstance(subject, str) or not subject.strip():
        raise PermissionError("trusted_subject_missing")
    _valid_id(workspace, "workspace_id")
    return {"subject": subject, "workspace_id": workspace}


class EntityGovernanceRegistry:
    """SQLite-backed permission request, approval, suspension, and revocation.

    authenticate(session) -> trusted principal {authenticated, subject, workspace_id}
    resolve_owner(workspace_id, entity_id) -> trusted owner subject or None
    authorize_governance(principal, entity_id, operation) -> bool

    Approval is a two-person control: the approver cannot be the requester.
    Grants are exact-scope, time-bounded, and immutable in their audit history.
    """

    def __init__(
        self,
        *,
        authenticate: Callable[[Any], dict[str, Any]],
        resolve_owner: Callable[[str, str], str | None],
        authorize_governance: Callable[[dict[str, Any], str, str], bool],
        db_path: str = ".xparallel/entity_governance.sqlite3",
    ):
        if not all(callable(x) for x in (authenticate, resolve_owner, authorize_governance)):
            raise TypeError("trusted_governance_adapters_required")
        self._authenticate = authenticate
        self._resolve_owner = resolve_owner
        self._authorize_governance = authorize_governance
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS entity_permission_grants (
                workspace_id TEXT NOT NULL,
                grant_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                requester_subject TEXT NOT NULL,
                approver_subject TEXT,
                key_id TEXT NOT NULL,
                capability_id TEXT NOT NULL,
                action TEXT NOT NULL,
                resource_scope TEXT NOT NULL,
                status TEXT NOT NULL,
                requested_at TEXT NOT NULL,
                decided_at TEXT,
                expires_at TEXT NOT NULL,
                reason TEXT,
                PRIMARY KEY (workspace_id, grant_id)
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS entity_grants_lookup
            ON entity_permission_grants(workspace_id, entity_id, status, expires_at)
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS entity_governance_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL,
                grant_id TEXT NOT NULL,
                actor_subject TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                detail_json TEXT NOT NULL
            )
        """)
        self._db.commit()

    def _get_principal(self, session: Any) -> dict[str, Any]:
        return _principal(self._authenticate(session))

    def _require_governance(self, principal: dict[str, Any], entity_id: str, operation: str) -> None:
        if self._authorize_governance(principal, entity_id, operation) is not True:
            raise PermissionError("governance_permission_denied")

    def _require_owner(self, principal: dict[str, Any], entity_id: str) -> None:
        owner = self._resolve_owner(principal["workspace_id"], entity_id)
        if not isinstance(owner, str) or owner != principal["subject"]:
            raise PermissionError("entity_owner_mismatch")

    def _event(self, workspace: str, grant_id: str, actor: str,
               event_type: str, detail: dict[str, Any], occurred_at: str) -> None:
        self._db.execute(
            """INSERT INTO entity_governance_events
               (workspace_id, grant_id, actor_subject, event_type, occurred_at, detail_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (workspace, grant_id, actor, event_type, occurred_at,
             json.dumps(detail, sort_keys=True, separators=(",", ":"))),
        )

    @staticmethod
    def _record(row: sqlite3.Row) -> dict[str, Any]:
        return {key: row[key] for key in (
            "workspace_id", "grant_id", "entity_id", "requester_subject",
            "approver_subject", "key_id", "capability_id", "action",
            "resource_scope", "status", "requested_at", "decided_at",
            "expires_at", "reason"
        )}

    def request_grant(
        self, session: Any, *, entity_id: str, key_id: str,
        capability_id: str, action: str, resource_scope: str,
        ttl_seconds: int = 3600,
    ) -> dict[str, Any]:
        principal = self._get_principal(session)
        entity = _valid_id(entity_id, "entity_id")
        key = _valid_id(key_id, "key_id")
        capability = _valid_id(capability_id, "capability_id")
        if not isinstance(action, str) or not _ID_RE.fullmatch(action):
            raise ValueError("invalid_action")
        if not isinstance(resource_scope, str) or not resource_scope.strip() or len(resource_scope) > _MAX_SCOPE_LENGTH:
            raise ValueError("invalid_resource_scope")
        if any(ch in resource_scope for ch in ("*", "\n", "\r")):
            raise ValueError("wildcard_or_multiline_scope_not_allowed")
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or not 60 <= ttl_seconds <= _MAX_TTL_SECONDS:
            raise ValueError("grant_ttl_out_of_range")
        self._require_owner(principal, entity)
        grant_id = "grant:" + uuid.uuid4().hex
        now = _now()
        expires = now + timedelta(seconds=ttl_seconds)
        with _LOCK, self._db:
            self._db.execute(
                """INSERT INTO entity_permission_grants
                   (workspace_id, grant_id, entity_id, requester_subject, key_id,
                    capability_id, action, resource_scope, status, requested_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (principal["workspace_id"], grant_id, entity, principal["subject"],
                 key, capability, action, resource_scope, _iso(now), _iso(expires)),
            )
            self._event(principal["workspace_id"], grant_id, principal["subject"],
                        "requested", {"key_id": key, "capability_id": capability,
                                      "action": action, "resource_scope": resource_scope,
                                      "expires_at": _iso(expires)}, _iso(now))
            row = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_id),
            ).fetchone()
        return self._record(row)

    def approve(self, session: Any, grant_id: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        grant_key = _valid_id(grant_id, "grant_id")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_key),
            ).fetchone()
            if row is None:
                raise ValueError("grant_not_found")
            if principal["subject"] == row["requester_subject"]:
                raise PermissionError("requester_cannot_approve_own_grant")
            self._require_governance(principal, row["entity_id"], "approve")
            if row["status"] != "pending":
                raise ValueError("grant_not_pending")
            now = _now()
            if datetime.fromisoformat(row["expires_at"]) <= now:
                raise ValueError("grant_request_expired")
            self._db.execute(
                """UPDATE entity_permission_grants SET status='approved',
                   approver_subject=?, decided_at=?
                   WHERE workspace_id=? AND grant_id=? AND status='pending'""",
                (principal["subject"], _iso(now), principal["workspace_id"], grant_key),
            )
            self._event(principal["workspace_id"], grant_key, principal["subject"],
                        "approved", {}, _iso(now))
            updated = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_key),
            ).fetchone()
        return self._record(updated)

    def _change_status(self, session: Any, grant_id: str, new_status: str,
                       operation: str, reason: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        grant_key = _valid_id(grant_id, "grant_id")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValueError("governance_reason_required")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_key),
            ).fetchone()
            if row is None:
                raise ValueError("grant_not_found")
            self._require_governance(principal, row["entity_id"], operation)
            if row["status"] not in {"approved", "suspended"}:
                raise ValueError("grant_not_active")
            if new_status == "suspended" and row["status"] != "approved":
                raise ValueError("grant_not_approved")
            if new_status == "revoked" and row["status"] == "revoked":
                raise ValueError("grant_already_revoked")
            now = _iso(_now())
            self._db.execute(
                """UPDATE entity_permission_grants SET status=?, decided_at=?, reason=?
                   WHERE workspace_id=? AND grant_id=?""",
                (new_status, now, reason.strip(), principal["workspace_id"], grant_key),
            )
            self._event(principal["workspace_id"], grant_key, principal["subject"],
                        new_status, {"reason": reason.strip()}, now)
            updated = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_key),
            ).fetchone()
        return self._record(updated)

    def suspend(self, session: Any, grant_id: str, reason: str) -> dict[str, Any]:
        return self._change_status(session, grant_id, "suspended", "suspend", reason)

    def reinstate(self, session: Any, grant_id: str, reason: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        grant_key = _valid_id(grant_id, "grant_id")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValueError("governance_reason_required")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_key),
            ).fetchone()
            if row is None:
                raise ValueError("grant_not_found")
            self._require_governance(principal, row["entity_id"], "reinstate")
            if row["status"] != "suspended":
                raise ValueError("grant_not_suspended")
            if datetime.fromisoformat(row["expires_at"]) <= _now():
                raise ValueError("grant_expired")
            now = _iso(_now())
            self._db.execute(
                """UPDATE entity_permission_grants SET status='approved', decided_at=?, reason=?
                   WHERE workspace_id=? AND grant_id=?""",
                (now, reason.strip(), principal["workspace_id"], grant_key),
            )
            self._event(principal["workspace_id"], grant_key, principal["subject"],
                        "reinstated", {"reason": reason.strip()}, now)
            updated = self._db.execute(
                "SELECT * FROM entity_permission_grants WHERE workspace_id=? AND grant_id=?",
                (principal["workspace_id"], grant_key),
            ).fetchone()
        return self._record(updated)

    def revoke(self, session: Any, grant_id: str, reason: str) -> dict[str, Any]:
        return self._change_status(session, grant_id, "revoked", "revoke", reason)

    def active_grants(self, workspace_id: str, entity_id: str,
                      *, now: datetime | None = None) -> list[dict[str, Any]]:
        workspace = _valid_id(workspace_id, "workspace_id")
        entity = _valid_id(entity_id, "entity_id")
        current = now or _now()
        if current.tzinfo is None:
            raise ValueError("timezone_aware_clock_required")
        with _LOCK:
            rows = self._db.execute(
                """SELECT * FROM entity_permission_grants
                   WHERE workspace_id=? AND entity_id=? AND status='approved'
                   AND expires_at>? ORDER BY requested_at""",
                (workspace, entity, _iso(current)),
            ).fetchall()
        return [{
            "grant_id": row["grant_id"], "workspace_id": row["workspace_id"],
            "entity_id": row["entity_id"], "subject": row["requester_subject"],
            "key_id": row["key_id"], "capability_id": row["capability_id"],
            "action": row["action"], "resource_scope": row["resource_scope"],
            "status": "approved", "expires_at": row["expires_at"],
        } for row in rows]

    def get(self, session: Any, grant_id: str) -> dict[str, Any] | None:
        principal = self._get_principal(session)
        grant_key = _valid_id(grant_id, "grant_id")
        with _LOCK:
            row = self._db.execute(
                """SELECT * FROM entity_permission_grants
                   WHERE workspace_id=? AND grant_id=?""",
                (principal["workspace_id"], grant_key),
            ).fetchone()
            if row is None:
                return None
            owner = self._resolve_owner(principal["workspace_id"], row["entity_id"])
            allowed = owner == principal["subject"] or self._authorize_governance(
                principal, row["entity_id"], "audit"
            )
            if not allowed:
                raise PermissionError("grant_read_forbidden")
        return self._record(row)

    def events(self, session: Any, grant_id: str) -> list[dict[str, Any]]:
        principal = self._get_principal(session)
        grant_key = _valid_id(grant_id, "grant_id")
        with _LOCK:
            grant = self._db.execute(
                """SELECT entity_id FROM entity_permission_grants
                   WHERE workspace_id=? AND grant_id=?""",
                (principal["workspace_id"], grant_key),
            ).fetchone()
            if grant is None:
                return []
            owner = self._resolve_owner(principal["workspace_id"], grant["entity_id"])
            allowed = owner == principal["subject"] or self._authorize_governance(principal, grant["entity_id"], "audit")
            if not allowed:
                raise PermissionError("grant_audit_forbidden")
            rows = self._db.execute(
                """SELECT actor_subject, event_type, occurred_at, detail_json
                   FROM entity_governance_events WHERE workspace_id=? AND grant_id=?
                   ORDER BY event_id""",
                (principal["workspace_id"], grant_key),
            ).fetchall()
        return [{"actor_subject": r["actor_subject"], "event_type": r["event_type"],
                 "occurred_at": r["occurred_at"], "detail": json.loads(r["detail_json"])}
                for r in rows]

    def close(self) -> None:
        with _LOCK:
            self._db.close()
