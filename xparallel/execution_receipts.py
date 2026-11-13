"""Signed, hash-chained execution receipts for XParallel.

Signing keys and authoritative job lookup remain host supplied. The local
SQLite chain is tamper-evident and detectable, not independently immutable.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_LOCK = threading.RLock()
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_ZERO_HASH = "0" * 64
_USAGE_KEYS = {"wall_ms", "cpu_ms", "memory_peak_mb", "output_bytes", "pids_peak"}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _id(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


def _digest(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"{field}_must_be_sha256")
    return value


def _timestamp(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"invalid_{field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"timezone_required:{field}")
    return parsed.astimezone(timezone.utc).isoformat()


def _principal(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or value.get("authenticated") is not True:
        raise PermissionError("caller_not_authenticated")
    subject, workspace = value.get("subject"), value.get("workspace_id")
    if not isinstance(subject, str) or not subject.strip():
        raise PermissionError("trusted_subject_missing")
    return {"subject": subject, "workspace_id": _id(workspace, "workspace_id")}


class ExecutionReceiptLedger:
    """Append-only receipt chain with injected identity, job lookup and signing.

    resolve_job(workspace_id, intent_id) returns the authoritative M2.12
    execution record. It must not accept caller-provided job details.
    sign_digest(digest_bytes) returns a detached signature string.
    verify_signature(digest_bytes, signature) returns True only for the trusted
    signing key. Private signing keys must remain outside this database.
    """

    def __init__(
        self, *,
        authenticate: Callable[[Any], dict[str, Any]],
        authorize_writer: Callable[[dict[str, str], dict[str, Any]], bool],
        resolve_job: Callable[[str, str], dict[str, Any] | None],
        sign_digest: Callable[[bytes], str],
        verify_signature: Callable[[bytes, str], bool],
        db_path: str = ".xparallel/execution_receipts.sqlite3",
    ):
        adapters = (authenticate, authorize_writer, resolve_job, sign_digest, verify_signature)
        if not all(callable(x) for x in adapters):
            raise TypeError("trusted_receipt_adapters_required")
        self._authenticate = authenticate
        self._authorize_writer = authorize_writer
        self._resolve_job = resolve_job
        self._sign = sign_digest
        self._verify_signature = verify_signature
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS execution_receipts (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL, receipt_id TEXT NOT NULL UNIQUE,
                intent_id TEXT NOT NULL, receipt_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL, receipt_hash TEXT NOT NULL UNIQUE,
                signature TEXT NOT NULL, recorded_at TEXT NOT NULL,
                UNIQUE(workspace_id, intent_id)
            )
        """)
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS execution_receipts_no_update
            BEFORE UPDATE ON execution_receipts BEGIN
                SELECT RAISE(ABORT, 'execution_receipts_are_append_only');
            END
        """)
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS execution_receipts_no_delete
            BEFORE DELETE ON execution_receipts BEGIN
                SELECT RAISE(ABORT, 'execution_receipts_are_append_only');
            END
        """)
        self._db.commit()

    def _principal(self, session: Any) -> dict[str, str]:
        return _principal(self._authenticate(session))

    @staticmethod
    def _validate_usage(usage: Any, limits: dict[str, Any]) -> dict[str, int]:
        if not isinstance(usage, dict) or set(usage) != _USAGE_KEYS:
            raise ValueError("resource_usage_schema_mismatch")
        for key, value in usage.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"invalid_resource_usage:{key}")
        bounds = {
            "wall_ms": limits["timeout_seconds"] * 1000,
            "cpu_ms": limits["timeout_seconds"] * max(1, limits["cpu_millis"] // 1000) * 1000,
            "memory_peak_mb": limits["memory_mb"],
            "output_bytes": limits["output_bytes"],
            "pids_peak": limits["pids"],
        }
        if any(usage[key] > bounds[key] for key in _USAGE_KEYS):
            raise ValueError("resource_usage_exceeds_approved_limits")
        return {key: usage[key] for key in sorted(_USAGE_KEYS)}

    def append(
        self, session: Any, *, intent_id: str, policy_decision: dict[str, Any],
        started_at: str, finished_at: str, exit_code: int,
        resource_usage: dict[str, Any], evidence_refs: list[str],
    ) -> dict[str, Any]:
        principal = self._principal(session)
        intent_key = _id(intent_id, "intent_id")
        job = self._resolve_job(principal["workspace_id"], intent_key)
        if not isinstance(job, dict):
            raise LookupError("authoritative_execution_record_not_found")
        if job.get("workspace_id") != principal["workspace_id"] or job.get("intent_id") != intent_key:
            raise ValueError("authoritative_execution_record_scope_mismatch")
        if job.get("status") != "finalizing":
            raise ValueError("execution_must_be_finalizing_before_receipt")
        if not isinstance(job.get("intent"), dict):
            raise ValueError("authoritative_job_intent_missing")
        if self._authorize_writer(principal, job) is not True:
            raise PermissionError("receipt_writer_not_authorized")

        intent = job["intent"]
        for field in ("payload_digest", "artifact_digest", "runner_image_digest"):
            _digest(intent.get(field), field)
        intent_digest = _digest(job.get("intent_digest"), "intent_digest")
        approver = job.get("approver_subject")
        if not isinstance(approver, str) or not approver.strip():
            raise ValueError("approved_human_identity_missing")
        approved_at = _timestamp(job.get("decided_at"), "approved_at")
        job_started = _timestamp(job.get("started_at"), "job_started_at")
        job_finished = _timestamp(job.get("finished_at"), "job_finished_at")
        supplied_started = _timestamp(started_at, "started_at")
        supplied_finished = _timestamp(finished_at, "finished_at")
        if supplied_started != job_started or supplied_finished != job_finished:
            raise ValueError("receipt_timestamps_do_not_match_job_record")
        if datetime.fromisoformat(job_finished) < datetime.fromisoformat(job_started):
            raise ValueError("execution_finished_before_start")

        if not isinstance(policy_decision, dict) or policy_decision.get("allowed") is not True:
            raise ValueError("successful_policy_decision_required")
        grant_id = _id(policy_decision.get("grant_id"), "grant_id")
        evidence_run_id = _id(policy_decision.get("evidence_run_id"), "evidence_run_id")
        if not isinstance(exit_code, int) or isinstance(exit_code, bool) or not 0 <= exit_code <= 255:
            raise ValueError("invalid_exit_code")
        if (job.get("outcome") == "success") != (exit_code == 0):
            raise ValueError("exit_code_does_not_match_job_outcome")
        usage = self._validate_usage(resource_usage, intent.get("limits", {}))
        if not isinstance(evidence_refs, list) or not 1 <= len(evidence_refs) <= 100:
            raise ValueError("evidence_refs_required")
        refs = []
        for ref in evidence_refs:
            if not isinstance(ref, str) or not ref.strip() or len(ref) > 1000:
                raise ValueError("invalid_evidence_reference")
            refs.append(ref.strip())

        receipt = {
            "schema_version": "1.0.0",
            "receipt_id": "receipt:" + uuid.uuid4().hex,
            "workspace_id": principal["workspace_id"],
            "intent_id": intent_key,
            "intent_digest": intent_digest,
            "entity_id": intent.get("entity_id"),
            "key_id": intent.get("key_id"),
            "capability_id": intent.get("capability_id"),
            "action": intent.get("action"),
            "resource_scope": intent.get("resource_scope"),
            "payload_digest": intent["payload_digest"],
            "artifact_digest": intent["artifact_digest"],
            "runner_image_digest": intent["runner_image_digest"],
            "approval": {"approver_subject": approver, "approved_at": approved_at},
            "policy_decision": {"allowed": True, "grant_id": grant_id,
                                "evidence_run_id": evidence_run_id},
            "started_at": job_started, "finished_at": job_finished,
            "exit_code": exit_code, "outcome": job.get("outcome"),
            "resource_usage": usage, "evidence_refs": refs,
        }
        canonical = _canonical(receipt)
        now = datetime.now(timezone.utc).isoformat()
        with _LOCK, self._db:
            previous = self._db.execute(
                """SELECT receipt_hash FROM execution_receipts
                   WHERE workspace_id=? ORDER BY sequence DESC LIMIT 1""",
                (principal["workspace_id"],),
            ).fetchone()
            previous_hash = previous["receipt_hash"] if previous else _ZERO_HASH
            receipt_hash = hashlib.sha256(
                bytes.fromhex(previous_hash) + canonical.encode("utf-8")
            ).hexdigest()
            signature = self._sign(bytes.fromhex(receipt_hash))
            if not isinstance(signature, str) or not signature:
                raise ValueError("trusted_receipt_signature_missing")
            self._db.execute(
                """INSERT INTO execution_receipts
                   (workspace_id, receipt_id, intent_id, receipt_json, previous_hash,
                    receipt_hash, signature, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (principal["workspace_id"], receipt["receipt_id"], intent_key,
                 canonical, previous_hash, receipt_hash, signature, now),
            )
            sequence = self._db.execute("SELECT last_insert_rowid()").fetchone()[0]
        return {"sequence": sequence, "receipt": receipt,
                "previous_hash": previous_hash, "receipt_hash": receipt_hash,
                "signature": signature, "recorded_at": now}

    def verify_chain(self, session: Any) -> dict[str, Any]:
        principal = self._principal(session)
        with _LOCK:
            rows = self._db.execute(
                """SELECT sequence, receipt_json, previous_hash, receipt_hash, signature
                   FROM execution_receipts WHERE workspace_id=? ORDER BY sequence""",
                (principal["workspace_id"],),
            ).fetchall()
        previous_hash = _ZERO_HASH
        verified = 0
        for row in rows:
            if row["previous_hash"] != previous_hash:
                return {"valid": False, "verified_count": verified,
                        "failed_sequence": row["sequence"], "reason": "previous_hash_mismatch"}
            expected = hashlib.sha256(
                bytes.fromhex(previous_hash) + row["receipt_json"].encode("utf-8")
            ).hexdigest()
            if expected != row["receipt_hash"]:
                return {"valid": False, "verified_count": verified,
                        "failed_sequence": row["sequence"], "reason": "receipt_hash_mismatch"}
            try:
                signature_ok = self._verify_signature(bytes.fromhex(expected), row["signature"]) is True
            except Exception:
                signature_ok = False
            if not signature_ok:
                return {"valid": False, "verified_count": verified,
                        "failed_sequence": row["sequence"], "reason": "signature_invalid"}
            previous_hash = expected
            verified += 1
        return {"valid": True, "verified_count": verified,
                "head_hash": previous_hash, "external_anchor": "not_configured"}

    def list_receipts(self, session: Any, limit: int = 100) -> list[dict[str, Any]]:
        principal = self._principal(session)
        bounded = max(1, min(int(limit), 500))
        with _LOCK:
            rows = self._db.execute(
                """SELECT sequence, receipt_json, previous_hash, receipt_hash,
                   signature, recorded_at FROM execution_receipts
                   WHERE workspace_id=? ORDER BY sequence DESC LIMIT ?""",
                (principal["workspace_id"], bounded),
            ).fetchall()
        return [{
            "sequence": row["sequence"], "receipt": json.loads(row["receipt_json"]),
            "previous_hash": row["previous_hash"], "receipt_hash": row["receipt_hash"],
            "signature": row["signature"], "recorded_at": row["recorded_at"],
        } for row in rows]

    def close(self) -> None:
        with _LOCK:
            self._db.close()
