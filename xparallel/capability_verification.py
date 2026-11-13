"""Evidence-based XParallel capability verification laboratory.

This stores independently executed verification outcomes. The host must supply
trusted authentication, verifier authorization, a trusted test-plan resolver,
and an isolated execution adapter. This module never executes submitted code.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

_LOCK = threading.RLock()
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_MAX_EXPIRY = 30 * 24 * 60 * 60
_MAX_CASES = 200


def _utcnow() -> datetime:
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
    if not isinstance(subject, str) or not subject.strip():
        raise PermissionError("trusted_subject_missing")
    return {"subject": subject, "workspace_id": _id(workspace, "workspace_id")}


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class CapabilityVerificationLab:
    """Append-only capability test runs with trusted verifier/sandbox adapters.

    authenticate(session) -> {authenticated: True, subject, workspace_id}
    authorize_verifier(principal, entity_id, capability_id, operation) -> bool
    resolve_test_plan(plan_id, plan_version, entity_id, capability_id) -> {
        plan_id, version, case_ids: [stable test case IDs]
    }
    execute_tests(entity_id, capability_id, capability_version, artifact_digest, plan)
        -> {cases: [{case_id, status: pass|fail|blocked, evidence_ref}]}

    execute_tests MUST run in a separately hardened sandbox with quotas, no
    ambient credentials, controlled network, and artifact isolation. This
    module cannot prove that the adapter is correctly sandboxed.
    """

    def __init__(
        self,
        *,
        authenticate: Callable[[Any], dict[str, Any]],
        authorize_verifier: Callable[[dict[str, str], str, str, str], bool],
        resolve_test_plan: Callable[[str, str, str, str], dict[str, Any]],
        execute_tests: Callable[[str, str, str, str, dict[str, Any]], dict[str, Any]],
        db_path: str = ".xparallel/capability_verification.sqlite3",
    ):
        adapters = (authenticate, authorize_verifier, resolve_test_plan, execute_tests)
        if not all(callable(adapter) for adapter in adapters):
            raise TypeError("trusted_verification_adapters_required")
        self._authenticate = authenticate
        self._authorize = authorize_verifier
        self._resolve_plan = resolve_test_plan
        self._execute = execute_tests
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS capability_verification_runs (
                workspace_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                capability_id TEXT NOT NULL,
                capability_version TEXT NOT NULL,
                artifact_digest TEXT NOT NULL,
                plan_id TEXT NOT NULL,
                plan_version TEXT NOT NULL,
                verifier_subject TEXT NOT NULL,
                outcome TEXT NOT NULL,
                case_results_json TEXT NOT NULL,
                evidence_digest TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                PRIMARY KEY (workspace_id, run_id)
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS capability_runs_latest
            ON capability_verification_runs(workspace_id, entity_id, capability_id, completed_at)
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS capability_verification_controls (
                workspace_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                capability_id TEXT NOT NULL,
                capability_version TEXT NOT NULL,
                status TEXT NOT NULL,
                actor_subject TEXT NOT NULL,
                reason TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                PRIMARY KEY (workspace_id, entity_id, capability_id, capability_version)
            )
        """)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS capability_verification_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                capability_id TEXT NOT NULL,
                actor_subject TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                detail_json TEXT NOT NULL
            )
        """)
        self._db.commit()

    def _principal(self, session: Any) -> dict[str, str]:
        return _principal(self._authenticate(session))

    def _authorize_verifier(self, principal: dict[str, str], entity: str,
                            capability: str, operation: str) -> None:
        if self._authorize(principal, entity, capability, operation) is not True:
            raise PermissionError("capability_verifier_permission_denied")

    def _event(self, workspace: str, entity: str, capability: str,
               actor: str, event: str, detail: dict[str, Any], now: str) -> None:
        self._db.execute(
            """INSERT INTO capability_verification_events
               (workspace_id, entity_id, capability_id, actor_subject,
                event_type, occurred_at, detail_json)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (workspace, entity, capability, actor, event, now, _canonical(detail)),
        )

    @staticmethod
    def _run_record(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "workspace_id": row["workspace_id"], "run_id": row["run_id"],
            "entity_id": row["entity_id"], "capability_id": row["capability_id"],
            "capability_version": row["capability_version"],
            "artifact_digest": row["artifact_digest"], "plan_id": row["plan_id"],
            "plan_version": row["plan_version"], "verifier_subject": row["verifier_subject"],
            "outcome": row["outcome"], "case_results": json.loads(row["case_results_json"]),
            "evidence_digest": row["evidence_digest"], "started_at": row["started_at"],
            "completed_at": row["completed_at"], "expires_at": row["expires_at"],
        }

    @staticmethod
    def _validate_plan(plan: Any, plan_id: str, plan_version: str) -> list[str]:
        if not isinstance(plan, dict) or plan.get("plan_id") != plan_id or plan.get("version") != plan_version:
            raise ValueError("trusted_test_plan_mismatch")
        case_ids = plan.get("case_ids")
        if (not isinstance(case_ids, list) or not 1 <= len(case_ids) <= _MAX_CASES
                or any(not isinstance(x, str) or not _ID.fullmatch(x) for x in case_ids)
                or len(set(case_ids)) != len(case_ids)):
            raise ValueError("invalid_trusted_test_plan_cases")
        return case_ids

    @staticmethod
    def _validate_results(results: Any, expected: list[str]) -> tuple[list[dict[str, str]], str]:
        if not isinstance(results, dict) or not isinstance(results.get("cases"), list):
            raise ValueError("invalid_sandbox_result")
        normalized = []
        seen = set()
        for item in results["cases"]:
            if not isinstance(item, dict):
                raise ValueError("invalid_sandbox_case_result")
            case_id, status, evidence = item.get("case_id"), item.get("status"), item.get("evidence_ref")
            if case_id not in expected or case_id in seen:
                raise ValueError("unexpected_or_duplicate_test_case")
            if status not in {"pass", "fail", "blocked"}:
                raise ValueError("invalid_test_case_status")
            if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 1000:
                raise ValueError("test_case_evidence_required")
            seen.add(case_id)
            normalized.append({"case_id": case_id, "status": status, "evidence_ref": evidence})
        if seen != set(expected):
            raise ValueError("incomplete_test_case_results")
        normalized.sort(key=lambda x: x["case_id"])
        digest = hashlib.sha256(_canonical(normalized).encode("utf-8")).hexdigest()
        return normalized, digest

    def run(
        self, session: Any, *, entity_id: str, capability_id: str,
        capability_version: str, artifact_digest: str,
        plan_id: str, plan_version: str, expires_in_seconds: int = 7 * 24 * 60 * 60,
    ) -> dict[str, Any]:
        principal = self._principal(session)
        entity = _id(entity_id, "entity_id")
        capability = _id(capability_id, "capability_id")
        plan_key = _id(plan_id, "plan_id")
        if not isinstance(capability_version, str) or not capability_version.strip() or len(capability_version) > 40:
            raise ValueError("invalid_capability_version")
        if not isinstance(plan_version, str) or not plan_version.strip() or len(plan_version) > 40:
            raise ValueError("invalid_plan_version")
        if not isinstance(artifact_digest, str) or not _SHA256.fullmatch(artifact_digest):
            raise ValueError("artifact_digest_must_be_sha256")
        if (not isinstance(expires_in_seconds, int) or isinstance(expires_in_seconds, bool)
                or not 60 <= expires_in_seconds <= _MAX_EXPIRY):
            raise ValueError("verification_expiry_out_of_range")
        self._authorize_verifier(principal, entity, capability, "run")
        plan = self._resolve_plan(plan_key, plan_version, entity, capability)
        expected_cases = self._validate_plan(plan, plan_key, plan_version)
        started = _utcnow()
        raw_results = self._execute(entity, capability, capability_version, artifact_digest, plan)
        completed = _utcnow()
        cases, evidence_digest = self._validate_results(raw_results, expected_cases)
        outcome = "passed" if all(x["status"] == "pass" for x in cases) else (
            "failed" if any(x["status"] == "fail" for x in cases) else "inconclusive"
        )
        expires = completed + timedelta(seconds=expires_in_seconds)
        run_id = "vrun:" + uuid.uuid4().hex
        with _LOCK, self._db:
            control = self._db.execute(
                """SELECT status FROM capability_verification_controls
                   WHERE workspace_id=? AND entity_id=? AND capability_id=? AND capability_version=?""",
                (principal["workspace_id"], entity, capability, capability_version),
            ).fetchone()
            if control and control["status"] == "revoked":
                raise PermissionError("capability_version_revoked")
            now = _iso(completed)
            self._db.execute(
                """INSERT INTO capability_verification_runs
                   (workspace_id, run_id, entity_id, capability_id, capability_version,
                    artifact_digest, plan_id, plan_version, verifier_subject, outcome,
                    case_results_json, evidence_digest, started_at, completed_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (principal["workspace_id"], run_id, entity, capability, capability_version,
                 artifact_digest, plan_key, plan_version, principal["subject"], outcome,
                 _canonical(cases), evidence_digest, _iso(started), now, _iso(expires)),
            )
            self._event(principal["workspace_id"], entity, capability, principal["subject"],
                        "verification_" + outcome,
                        {"run_id": run_id, "artifact_digest": artifact_digest,
                         "capability_version": capability_version, "plan_id": plan_key,
                         "plan_version": plan_version, "evidence_digest": evidence_digest}, now)
            row = self._db.execute(
                "SELECT * FROM capability_verification_runs WHERE workspace_id=? AND run_id=?",
                (principal["workspace_id"], run_id),
            ).fetchone()
        return self._run_record(row)

    def set_control(self, session: Any, *, entity_id: str, capability_id: str,
                    capability_version: str, status: str, reason: str) -> dict[str, str]:
        principal = self._principal(session)
        entity = _id(entity_id, "entity_id")
        capability = _id(capability_id, "capability_id")
        if status not in {"suspended", "revoked"}:
            raise ValueError("invalid_capability_control_status")
        if not isinstance(capability_version, str) or not capability_version.strip():
            raise ValueError("invalid_capability_version")
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValueError("capability_control_reason_required")
        self._authorize_verifier(principal, entity, capability, status)
        now = _iso(_utcnow())
        with _LOCK, self._db:
            previous = self._db.execute(
                """SELECT status FROM capability_verification_controls
                   WHERE workspace_id=? AND entity_id=? AND capability_id=? AND capability_version=?""",
                (principal["workspace_id"], entity, capability, capability_version),
            ).fetchone()
            if previous and previous["status"] == "revoked":
                raise ValueError("capability_version_already_revoked")
            if previous and previous["status"] == "suspended" and status == "suspended":
                raise ValueError("capability_already_suspended")
            self._db.execute(
                """INSERT INTO capability_verification_controls
                   (workspace_id, entity_id, capability_id, capability_version,
                    status, actor_subject, reason, changed_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(workspace_id, entity_id, capability_id, capability_version)
                   DO UPDATE SET status=excluded.status, actor_subject=excluded.actor_subject,
                                 reason=excluded.reason, changed_at=excluded.changed_at""",
                (principal["workspace_id"], entity, capability, capability_version,
                 status, principal["subject"], reason.strip(), now),
            )
            self._event(principal["workspace_id"], entity, capability, principal["subject"],
                        "capability_" + status,
                        {"capability_version": capability_version, "reason": reason.strip()}, now)
        return {"workspace_id": principal["workspace_id"], "entity_id": entity,
                "capability_id": capability, "capability_version": capability_version,
                "status": status, "changed_at": now}

    def status(self, workspace_id: str, entity_id: str, capability_id: str,
               capability_version: str, artifact_digest: str,
               *, now: datetime | None = None) -> dict[str, Any]:
        workspace = _id(workspace_id, "workspace_id")
        entity = _id(entity_id, "entity_id")
        capability = _id(capability_id, "capability_id")
        if not isinstance(artifact_digest, str) or not _SHA256.fullmatch(artifact_digest):
            raise ValueError("artifact_digest_must_be_sha256")
        current = now or _utcnow()
        if current.tzinfo is None:
            raise ValueError("timezone_aware_clock_required")
        with _LOCK:
            control = self._db.execute(
                """SELECT status, reason, changed_at FROM capability_verification_controls
                   WHERE workspace_id=? AND entity_id=? AND capability_id=? AND capability_version=?""",
                (workspace, entity, capability, capability_version),
            ).fetchone()
            if control:
                return {"status": control["status"], "reason": control["reason"],
                        "changed_at": control["changed_at"], "run_id": None}
            row = self._db.execute(
                """SELECT * FROM capability_verification_runs
                   WHERE workspace_id=? AND entity_id=? AND capability_id=? AND capability_version=?
                   ORDER BY completed_at DESC LIMIT 1""",
                (workspace, entity, capability, capability_version),
            ).fetchone()
        if row is None:
            return {"status": "unverified", "reason": "no_verification_run", "run_id": None}
        if row["artifact_digest"] != artifact_digest:
            return {"status": "unverified", "reason": "artifact_digest_changed", "run_id": row["run_id"]}
        if datetime.fromisoformat(row["expires_at"]) <= current.astimezone(timezone.utc):
            return {"status": "expired", "reason": "verification_expired", "run_id": row["run_id"]}
        if row["outcome"] != "passed":
            return {"status": row["outcome"], "reason": "latest_verification_not_passed", "run_id": row["run_id"]}
        return {"status": "verified", "reason": "all_trusted_test_cases_passed",
                "run_id": row["run_id"], "evidence_digest": row["evidence_digest"],
                "expires_at": row["expires_at"], "artifact_digest": row["artifact_digest"]}

    def get_run(self, session: Any, run_id: str) -> dict[str, Any] | None:
        principal = self._principal(session)
        key = _id(run_id, "run_id")
        with _LOCK:
            row = self._db.execute(
                "SELECT * FROM capability_verification_runs WHERE workspace_id=? AND run_id=?",
                (principal["workspace_id"], key),
            ).fetchone()
            if row is None:
                return None
            self._authorize_verifier(principal, row["entity_id"], row["capability_id"], "read")
            return self._run_record(row)

    def events(self, session: Any, entity_id: str, capability_id: str) -> list[dict[str, Any]]:
        principal = self._principal(session)
        entity = _id(entity_id, "entity_id")
        capability = _id(capability_id, "capability_id")
        self._authorize_verifier(principal, entity, capability, "audit")
        with _LOCK:
            rows = self._db.execute(
                """SELECT actor_subject, event_type, occurred_at, detail_json
                   FROM capability_verification_events
                   WHERE workspace_id=? AND entity_id=? AND capability_id=?
                   ORDER BY event_id""",
                (principal["workspace_id"], entity, capability),
            ).fetchall()
        return [{"actor_subject": r["actor_subject"], "event_type": r["event_type"],
                 "occurred_at": r["occurred_at"], "detail": json.loads(r["detail_json"])}
                for r in rows]

    def close(self) -> None:
        with _LOCK:
            self._db.close()
