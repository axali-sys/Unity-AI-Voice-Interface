"""Workspace-scoped, content-addressed execution evidence on persistent SQLite.

This is a local persistent-volume adapter. It is not encrypted, externally
anchored, or a substitute for managed object storage with retention controls.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Callable

from xparallel.execution_host_services import _required_sha

_LOCK = threading.RLock()
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,199}$")
_MAX_EVIDENCE_BYTES = 2 * 1024 * 1024


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


class SQLiteExecutionEvidenceStore:
    """Append-only evidence blobs with workspace-bound retrieval.

    sanitize_result is mandatory to prevent accidental persistence of secrets.
    The sanitizer is a host trust boundary and must be tested for the app's
    output formats. Evidence is integrity checked, not confidential/encrypted.
    """

    def __init__(
        self, *, authenticate: Callable[[Any], dict[str, Any]],
        authorize_read: Callable[[dict[str, str], dict[str, Any]], bool],
        sanitize_result: Callable[[dict[str, Any]], dict[str, Any]],
        db_path: str = ".xparallel/execution_evidence.sqlite3",
    ):
        if not all(callable(x) for x in (authenticate, authorize_read, sanitize_result)):
            raise TypeError("trusted_evidence_store_adapters_required")
        self._authenticate = authenticate
        self._authorize_read = authorize_read
        self._sanitize = sanitize_result
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS execution_evidence (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                workspace_id TEXT NOT NULL,
                intent_id TEXT NOT NULL,
                evidence_digest TEXT NOT NULL,
                evidence_json BLOB NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                UNIQUE(workspace_id, intent_id, evidence_digest)
            )
        """)
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS execution_evidence_no_update
            BEFORE UPDATE ON execution_evidence BEGIN
                SELECT RAISE(ABORT, 'execution_evidence_is_append_only');
            END
        """)
        self._db.execute("""
            CREATE TRIGGER IF NOT EXISTS execution_evidence_no_delete
            BEFORE DELETE ON execution_evidence BEGIN
                SELECT RAISE(ABORT, 'execution_evidence_is_append_only');
            END
        """)
        self._db.commit()

    def _principal(self, session: Any) -> dict[str, str]:
        value = self._authenticate(session)
        if not isinstance(value, dict) or value.get("authenticated") is not True:
            raise PermissionError("caller_not_authenticated")
        subject, workspace = value.get("subject"), value.get("workspace_id")
        if not isinstance(subject, str) or not subject.strip():
            raise PermissionError("trusted_subject_missing")
        if not isinstance(workspace, str) or not _ID.fullmatch(workspace):
            raise PermissionError("trusted_workspace_missing")
        return {"subject": subject, "workspace_id": workspace}

    def store_evidence(
        self, result: dict[str, Any], intent: dict[str, Any]
    ) -> dict[str, Any]:
        if not isinstance(intent, dict):
            raise ValueError("authoritative_execution_intent_required")
        workspace = intent.get("workspace_id")
        intent_id = intent.get("intent_id")
        if not isinstance(workspace, str) or not _ID.fullmatch(workspace):
            raise ValueError("valid_intent_workspace_required")
        if not isinstance(intent_id, str) or not _ID.fullmatch(intent_id):
            raise ValueError("valid_intent_id_required")
        if not isinstance(result, dict):
            raise ValueError("execution_result_object_required")
        sanitized = self._sanitize(result)
        if not isinstance(sanitized, dict):
            raise ValueError("sanitized_execution_evidence_must_be_object")
        encoded = _canonical({
            "schema_version": "1.0.0",
            "workspace_id": workspace,
            "intent_id": intent_id,
            "result": sanitized,
        })
        if len(encoded) > _MAX_EVIDENCE_BYTES:
            raise ValueError("execution_evidence_exceeds_size_limit")
        digest = hashlib.sha256(encoded).hexdigest()
        with _LOCK, self._db:
            self._db.execute(
                """INSERT OR IGNORE INTO execution_evidence
                   (workspace_id, intent_id, evidence_digest, evidence_json)
                   VALUES (?, ?, ?, ?)""",
                (workspace, intent_id, digest, encoded),
            )
            row = self._db.execute(
                """SELECT sequence FROM execution_evidence
                   WHERE workspace_id=? AND intent_id=? AND evidence_digest=?""",
                (workspace, intent_id, digest),
            ).fetchone()
        if row is None:
            raise RuntimeError("execution_evidence_commit_not_confirmed")
        return {
            "durable": True,
            "references": [f"xpevidence://{workspace}/{intent_id}/{digest}"],
            "digest": digest,
            "sequence": row["sequence"],
            "storage": "sqlite-persistent-volume",
        }

    def read_evidence(self, session: Any, reference: str) -> dict[str, Any]:
        principal = self._principal(session)
        if not isinstance(reference, str) or not reference.startswith("xpevidence://"):
            raise ValueError("invalid_evidence_reference")
        parts = reference[len("xpevidence://"):].split("/")
        if len(parts) != 3:
            raise ValueError("invalid_evidence_reference")
        workspace, intent_id, digest = parts
        _required_sha(digest, "evidence_digest")
        if workspace != principal["workspace_id"]:
            raise PermissionError("evidence_workspace_mismatch")
        with _LOCK:
            row = self._db.execute(
                """SELECT evidence_json, sequence FROM execution_evidence
                   WHERE workspace_id=? AND intent_id=? AND evidence_digest=?""",
                (workspace, intent_id, digest),
            ).fetchone()
        if row is None:
            raise LookupError("execution_evidence_not_found")
        record = json.loads(bytes(row["evidence_json"]).decode("utf-8"))
        if hashlib.sha256(_canonical(record)).hexdigest() != digest:
            raise ValueError("execution_evidence_integrity_check_failed")
        if self._authorize_read(principal, record) is not True:
            raise PermissionError("evidence_read_not_authorized")
        return {"sequence": row["sequence"], "digest": digest, "record": record}

    def close(self) -> None:
        with _LOCK:
            self._db.close()
