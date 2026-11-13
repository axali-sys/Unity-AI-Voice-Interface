"""Human-approved, one-time XParallel execution tickets.

This module creates immutable job intents and approval-bound tickets. It does
not launch processes. A separate executor must poll the running ticket and
honor cancellation/revocation checks before and during execution.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

_LOCK = threading.RLock()
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_LIMITS = {
    "timeout_seconds": (1, 600),
    "memory_mb": (64, 2048),
    "cpu_millis": (100, 4000),
    "pids": (1, 1024),
    "output_bytes": (1024, 10_000_000),
}
_INTENT_STATES = {"requested", "approved", "denied", "running", "finalizing", "completed", "failed", "cancelled"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


def _principal(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or value.get("authenticated") is not True:
        raise PermissionError("caller_not_authenticated")
    subject = value.get("subject")
    workspace = value.get("workspace_id")
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 200:
        raise PermissionError("trusted_subject_missing")
    return {"subject": subject, "workspace_id": _id(workspace, "workspace_id")}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field}_must_be_sha256")
    return value


def _validate_limits(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != set(_LIMITS):
        raise ValueError("execution_limits_must_match_approved_schema")
    result: dict[str, int] = {}
    for key, (minimum, maximum) in _LIMITS.items():
        item = value[key]
        if not isinstance(item, int) or isinstance(item, bool) or not minimum <= item <= maximum:
            raise ValueError(f"execution_limit_out_of_range:{key}")
        result[key] = item
    return result


class ExecutionApprovalRegistry:
    """SQLite job-intent, separated-approval, one-use-ticket and lifecycle store.

    Required host adapters:
      authenticate(session) -> trusted {authenticated, subject, workspace_id}
      authorize_request(principal, intent) -> bool
      authorize_approval(principal, intent) -> bool
      authorize_cancel(principal, intent) -> bool
      authorize_executor(principal, intent) -> bool
      validate_current_state(principal, intent, stage) -> bool

    validate_current_state must re-check entity/key/capability/grant/artifact
    revocation at both start and every in-execution checkpoint. It must use
    authoritative server-side records, not request-body claims.
    """

    def __init__(
        self, *, authenticate: Callable[[Any], dict[str, Any]],
        authorize_request: Callable[[dict[str, str], dict[str, Any]], bool],
        authorize_approval: Callable[[dict[str, str], dict[str, Any]], bool],
        authorize_cancel: Callable[[dict[str, str], dict[str, Any]], bool],
        authorize_executor: Callable[[dict[str, str], dict[str, Any]], bool],
        validate_current_state: Callable[[dict[str, str], dict[str, Any], str], bool],
        db_path: str = ".xparallel/execution_approvals.sqlite3",
    ):
        adapters = (authenticate, authorize_request, authorize_approval,
                    authorize_cancel, authorize_executor, validate_current_state)
        if not all(callable(x) for x in adapters):
            raise TypeError("trusted_execution_approval_adapters_required")
        self._authenticate = authenticate
        self._authorize_request = authorize_request
        self._authorize_approval = authorize_approval
        self._authorize_cancel = authorize_cancel
        self._authorize_executor = authorize_executor
        self._validate_current = validate_current_state
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS execution_intents (
                workspace_id TEXT NOT NULL, intent_id TEXT NOT NULL,
                requester_subject TEXT NOT NULL, approver_subject TEXT,
                intent_json TEXT NOT NULL, intent_digest TEXT NOT NULL,
                status TEXT NOT NULL, requested_at TEXT NOT NULL,
                decided_at TEXT, expires_at TEXT NOT NULL,
                ticket_id TEXT, ticket_hash TEXT, ticket_expires_at TEXT,
                executor_subject TEXT, started_at TEXT, finished_at TEXT,
                outcome TEXT, cancellation_reason TEXT, finalization_json TEXT,
                PRIMARY KEY(workspace_id, intent_id),
                UNIQUE(workspace_id, ticket_id),
                UNIQUE(ticket_hash)
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS execution_intent_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL, intent_id TEXT NOT NULL,
                actor_subject TEXT NOT NULL, event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL, detail_json TEXT NOT NULL
            )
        """)
        columns = {row["name"] for row in self._db.execute("PRAGMA table_info(execution_intents)")}
        if "finalization_json" not in columns:
            self._db.execute("ALTER TABLE execution_intents ADD COLUMN finalization_json TEXT")
        self._db.commit()

    def _get_principal(self, session: Any) -> dict[str, str]:
        return _principal(self._authenticate(session))

    def _event(self, workspace: str, intent_id: str, actor: str,
               event: str, detail: dict[str, Any], at: datetime) -> None:
        self._db.execute(
            """INSERT INTO execution_intent_events
               (workspace_id, intent_id, actor_subject, event_type, occurred_at, detail_json)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (workspace, intent_id, actor, event, _iso(at), _canonical(detail)),
        )

    @staticmethod
    def _record(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "workspace_id": row["workspace_id"], "intent_id": row["intent_id"],
            "requester_subject": row["requester_subject"], "approver_subject": row["approver_subject"],
            "intent": json.loads(row["intent_json"]), "intent_digest": row["intent_digest"],
            "status": row["status"], "requested_at": row["requested_at"],
            "decided_at": row["decided_at"], "expires_at": row["expires_at"],
            "ticket_id": row["ticket_id"], "ticket_expires_at": row["ticket_expires_at"],
            "executor_subject": row["executor_subject"], "started_at": row["started_at"],
            "finished_at": row["finished_at"], "outcome": row["outcome"],
            "cancellation_reason": row["cancellation_reason"],
        }

    def request_intent(
        self, session: Any, *, entity_id: str, key_id: str,
        capability_id: str, action: str, resource_scope: str,
        payload_digest: str, artifact_digest: str, runner_image_digest: str,
        limits: dict[str, Any], ttl_seconds: int = 1800,
    ) -> dict[str, Any]:
        principal = self._get_principal(session)
        if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or not 60 <= ttl_seconds <= 3600:
            raise ValueError("intent_ttl_out_of_range")
        entity = _id(entity_id, "entity_id")
        key = _id(key_id, "key_id")
        capability = _id(capability_id, "capability_id")
        if not isinstance(action, str) or not _ID.fullmatch(action):
            raise ValueError("invalid_action")
        if not isinstance(resource_scope, str) or not resource_scope.strip() or len(resource_scope) > 500:
            raise ValueError("invalid_resource_scope")
        if any(x in resource_scope for x in ("*", "\n", "\r")):
            raise ValueError("wildcard_or_multiline_scope_not_allowed")
        normalized_limits = _validate_limits(limits)
        payload = _digest(payload_digest, "payload_digest")
        artifact = _digest(artifact_digest, "artifact_digest")
        image = _digest(runner_image_digest, "runner_image_digest")
        intent = {
            "schema_version": "1.0.0", "workspace_id": principal["workspace_id"],
            "entity_id": entity, "key_id": key, "capability_id": capability,
            "action": action, "resource_scope": resource_scope,
            "payload_digest": payload, "artifact_digest": artifact,
            "runner_image_digest": image, "limits": normalized_limits,
        }
        if self._authorize_request(principal, intent) is not True:
            raise PermissionError("execution_intent_not_authorized")
        canonical = _canonical(intent)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        now = _now()
        expires = now + timedelta(seconds=ttl_seconds)
        intent_id = "job:" + uuid.uuid4().hex
        with _LOCK, self._db:
            self._db.execute(
                """INSERT INTO execution_intents
                   (workspace_id, intent_id, requester_subject, intent_json, intent_digest,
                    status, requested_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, 'requested', ?, ?)""",
                (principal["workspace_id"], intent_id, principal["subject"],
                 canonical, digest, _iso(now), _iso(expires)),
            )
            self._event(principal["workspace_id"], intent_id, principal["subject"],
                        "intent_requested", {"intent_digest": digest}, now)
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], intent_id),
            ).fetchone()
        return self._record(row)

    def approve(self, session: Any, intent_id: str, *, reason: str,
                ticket_ttl_seconds: int = 600) -> dict[str, Any]:
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValueError("approval_reason_required")
        if not isinstance(ticket_ttl_seconds, int) or isinstance(ticket_ttl_seconds, bool) or not 30 <= ticket_ttl_seconds <= 900:
            raise ValueError("ticket_ttl_out_of_range")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None:
                raise LookupError("execution_intent_not_found")
            if row["status"] != "requested":
                raise ValueError("intent_not_pending_approval")
            if row["requester_subject"] == principal["subject"]:
                raise PermissionError("requester_cannot_approve_own_execution")
            intent = self._record(row)["intent"]
            if self._authorize_approval(principal, intent) is not True:
                raise PermissionError("execution_approval_not_authorized")
            now = _now()
            if datetime.fromisoformat(row["expires_at"]) <= now:
                raise ValueError("execution_intent_expired")
            token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
            ticket_id = "ticket:" + uuid.uuid4().hex
            ticket_expires = min(
                now + timedelta(seconds=ticket_ttl_seconds),
                datetime.fromisoformat(row["expires_at"]),
            )
            self._db.execute(
                """UPDATE execution_intents SET status='approved', approver_subject=?,
                   decided_at=?, ticket_id=?, ticket_hash=?, ticket_expires_at=?
                   WHERE workspace_id=? AND intent_id=? AND status='requested'""",
                (principal["subject"], _iso(now), ticket_id, token_hash,
                 _iso(ticket_expires), principal["workspace_id"], key),
            )
            self._event(principal["workspace_id"], key, principal["subject"],
                        "intent_approved", {"ticket_id": ticket_id, "reason": reason.strip(),
                                            "ticket_expires_at": _iso(ticket_expires)}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return {"intent": self._record(updated), "one_time_ticket": token}

    def deny(self, session: Any, intent_id: str, *, reason: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValueError("denial_reason_required")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None:
                raise LookupError("execution_intent_not_found")
            if row["status"] != "requested":
                raise ValueError("intent_not_pending_approval")
            if row["requester_subject"] == principal["subject"]:
                raise PermissionError("requester_cannot_decide_own_execution")
            intent = self._record(row)["intent"]
            if self._authorize_approval(principal, intent) is not True:
                raise PermissionError("execution_approval_not_authorized")
            now = _now()
            self._db.execute(
                """UPDATE execution_intents SET status='denied', approver_subject=?, decided_at=?
                   WHERE workspace_id=? AND intent_id=? AND status='requested'""",
                (principal["subject"], _iso(now), principal["workspace_id"], key),
            )
            self._event(principal["workspace_id"], key, principal["subject"],
                        "intent_denied", {"reason": reason.strip()}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return self._record(updated)

    def start(self, session: Any, one_time_ticket: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        if not isinstance(one_time_ticket, str) or not 32 <= len(one_time_ticket) <= 256:
            raise PermissionError("invalid_execution_ticket")
        token_hash = hashlib.sha256(one_time_ticket.encode("utf-8")).hexdigest()
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND ticket_hash=?",
                (principal["workspace_id"], token_hash),
            ).fetchone()
            if row is None or row["status"] != "approved":
                raise PermissionError("execution_ticket_invalid_or_already_used")
            now = _now()
            if datetime.fromisoformat(row["ticket_expires_at"]) <= now:
                raise PermissionError("execution_ticket_expired")
            intent = self._record(row)["intent"]
            if self._authorize_executor(principal, intent) is not True:
                raise PermissionError("executor_not_authorized")
            if self._validate_current(principal, intent, "start") is not True:
                raise PermissionError("execution_revoked_or_stale_before_start")
            self._db.execute(
                """UPDATE execution_intents SET status='running', executor_subject=?,
                   started_at=?, ticket_hash=NULL
                   WHERE workspace_id=? AND intent_id=? AND status='approved'""",
                (principal["subject"], _iso(now), principal["workspace_id"], row["intent_id"]),
            )
            self._event(principal["workspace_id"], row["intent_id"], principal["subject"],
                        "execution_started", {"ticket_id": row["ticket_id"],
                                              "intent_digest": row["intent_digest"]}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], row["intent_id"]),
            ).fetchone()
        return self._record(updated)

    def check_running(self, session: Any, intent_id: str) -> dict[str, Any]:
        """Checkpoint called before/during work; false means stop execution immediately."""
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        with _LOCK:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None or row["status"] != "running":
                raise PermissionError("execution_not_running")
            if row["executor_subject"] != principal["subject"]:
                raise PermissionError("execution_executor_mismatch")
            intent = self._record(row)["intent"]
            if self._validate_current(principal, intent, "during_execution") is not True:
                return {"continue": False, "reason": "execution_revoked_or_stale"}
            return {"continue": True, "reason": "execution_authorized"}

    def cancel(self, session: Any, intent_id: str, *, reason: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValueError("cancellation_reason_required")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None:
                raise LookupError("execution_intent_not_found")
            if row["status"] not in {"requested", "approved", "running"}:
                raise ValueError("execution_intent_not_cancellable")
            intent = self._record(row)["intent"]
            if self._authorize_cancel(principal, intent) is not True:
                raise PermissionError("execution_cancellation_not_authorized")
            now = _now()
            self._db.execute(
                """UPDATE execution_intents SET status='cancelled', cancellation_reason=?,
                   finished_at=?, ticket_hash=NULL
                   WHERE workspace_id=? AND intent_id=?""",
                (reason.strip(), _iso(now), principal["workspace_id"], key),
            )
            self._event(principal["workspace_id"], key, principal["subject"],
                        "execution_cancelled", {"reason": reason.strip(),
                                                "previous_status": row["status"]}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return self._record(updated)

    def begin_finalization(self, session: Any, intent_id: str, *, outcome: str, receipt_data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Freeze execution outcome while keeping the job non-terminal until receipt commit."""
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        if outcome not in {"success", "failure", "blocked"}:
            raise ValueError("invalid_execution_outcome")
        if receipt_data is not None:
            if not isinstance(receipt_data, dict) or set(receipt_data) != {
                "policy_decision", "started_at", "resource_usage", "evidence_refs"
            }:
                raise ValueError("invalid_finalization_receipt_data")
            encoded_receipt_data = _canonical(receipt_data)
            if len(encoded_receipt_data.encode("utf-8")) > 65536:
                raise ValueError("finalization_receipt_data_too_large")
        else:
            encoded_receipt_data = None
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None or row["status"] != "running":
                raise ValueError("execution_not_running")
            if row["executor_subject"] != principal["subject"]:
                raise PermissionError("execution_executor_mismatch")
            intent = self._record(row)["intent"]
            if outcome == "success" and self._validate_current(principal, intent, "finish") is not True:
                raise PermissionError("execution_revoked_or_stale_at_completion")
            now = _now()
            self._db.execute(
                """UPDATE execution_intents SET status='finalizing', outcome=?, finished_at=?, finalization_json=?
                   WHERE workspace_id=? AND intent_id=? AND status='running'""",
                (outcome, _iso(now), encoded_receipt_data, principal["workspace_id"], key),
            )
            self._event(principal["workspace_id"], key, principal["subject"],
                        "execution_finalizing", {"outcome": outcome}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return self._record(updated)

    def get_finalization_for_recovery(self, session: Any, intent_id: str) -> dict[str, Any]:
        """Return the immutable pending receipt package only to the bound executor."""
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        with _LOCK:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        if row is None:
            raise LookupError("execution_intent_not_found")
        if row["status"] != "finalizing":
            raise ValueError("execution_not_pending_finalization")
        if row["executor_subject"] != principal["subject"]:
            raise PermissionError("execution_executor_mismatch")
        if not row["finalization_json"]:
            raise ValueError("finalization_receipt_data_unavailable")
        record = self._record(row)
        record["finalization_data"] = json.loads(row["finalization_json"])
        return record

    def complete_finalization(self, session: Any, intent_id: str) -> dict[str, Any]:
        """Mark terminal only after a receipt exists and has been committed by the caller."""
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None or row["status"] != "finalizing":
                raise ValueError("execution_not_finalizing")
            if row["executor_subject"] != principal["subject"]:
                raise PermissionError("execution_executor_mismatch")
            outcome = row["outcome"]
            if outcome not in {"success", "failure", "blocked"} or not row["finished_at"]:
                raise ValueError("execution_finalization_record_incomplete")
            status = "completed" if outcome == "success" else "failed"
            now = _now()
            self._db.execute(
                """UPDATE execution_intents SET status=?
                   WHERE workspace_id=? AND intent_id=? AND status='finalizing'""",
                (status, principal["workspace_id"], key),
            )
            self._event(principal["workspace_id"], key, principal["subject"],
                        "execution_receipt_committed", {"outcome": outcome}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return self._record(updated)

    def finish(self, session: Any, intent_id: str, *, outcome: str) -> dict[str, Any]:
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        if outcome not in {"success", "failure", "blocked"}:
            raise ValueError("invalid_execution_outcome")
        with _LOCK, self._db:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None or row["status"] != "running":
                raise ValueError("execution_not_running")
            if row["executor_subject"] != principal["subject"]:
                raise PermissionError("execution_executor_mismatch")
            intent = self._record(row)["intent"]
            if outcome == "success" and self._validate_current(principal, intent, "finish") is not True:
                raise PermissionError("execution_revoked_or_stale_at_completion")
            now = _now()
            status = "completed" if outcome == "success" else "failed"
            self._db.execute(
                """UPDATE execution_intents SET status=?, outcome=?, finished_at=?
                   WHERE workspace_id=? AND intent_id=? AND status='running'""",
                (status, outcome, _iso(now), principal["workspace_id"], key),
            )
            self._event(principal["workspace_id"], key, principal["subject"],
                        "execution_" + outcome, {}, now)
            updated = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return self._record(updated)

    def get(self, session: Any, intent_id: str) -> dict[str, Any] | None:
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        with _LOCK:
            row = self._db.execute(
                "SELECT * FROM execution_intents WHERE workspace_id=? AND intent_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
        return self._record(row) if row else None

    def events(self, session: Any, intent_id: str) -> list[dict[str, Any]]:
        principal = self._get_principal(session)
        key = _id(intent_id, "intent_id")
        with _LOCK:
            rows = self._db.execute(
                """SELECT actor_subject, event_type, occurred_at, detail_json
                   FROM execution_intent_events WHERE workspace_id=? AND intent_id=?
                   ORDER BY event_id""",
                (principal["workspace_id"], key),
            ).fetchall()
        return [{"actor_subject": row["actor_subject"], "event_type": row["event_type"],
                 "occurred_at": row["occurred_at"], "detail": json.loads(row["detail_json"])}
                for row in rows]

    def close(self) -> None:
        with _LOCK:
            self._db.close()
