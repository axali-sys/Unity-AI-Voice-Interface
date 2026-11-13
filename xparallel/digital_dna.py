"""Local, workspace-scoped registry for versioned XParallel Digital DNA manifests.

This prototype validates manifest structure and records immutable revisions. It does
not authenticate owners, verify signatures, certify capabilities, or authorize execution.
Those remain separate security boundaries.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "0.1.0"
ENTITY_TYPES = {"agent", "service", "tool", "model", "device", "organization", "composite"}
ENTITY_STATUSES = {"pending", "active", "suspended", "revoked", "retired"}
CAPABILITY_STATUSES = {"declared", "under_review", "verified", "suspended", "revoked"}
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SECRET_KEY_PARTS = ("password", "secret", "token", "private_key", "api_key", "credential_value")
_LOCK = threading.RLock()


def _now() -> str:
    return datetime.now().astimezone().isoformat()


def _workspace(value: str) -> str:
    workspace = str(value or "").strip()
    if not workspace or len(workspace) > 200:
        raise ValueError("invalid_workspace_id")
    return workspace


def _object(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name}_must_be_object")
    return value


def _no_secret_fields(value: Any, path: str = "manifest") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in SECRET_KEY_PARTS):
                raise ValueError(f"secret_field_not_allowed:{path}.{key}")
            _no_secret_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _no_secret_fields(child, f"{path}[{index}]")


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate the required Digital DNA 0.1 contract fields and safety invariants."""
    data = _object(manifest, "manifest")
    required = {
        "schema_version", "entity_id", "entity_type", "display_name", "issuer",
        "status", "created_at", "updated_at", "owner", "protocols",
        "capabilities", "permission_requests", "data_handling",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ValueError("missing_required_fields:" + ",".join(missing))
    if data["schema_version"] != SCHEMA_VERSION:
        raise ValueError("unsupported_schema_version")
    entity_id = data["entity_id"]
    if not isinstance(entity_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{7,199}", entity_id):
        raise ValueError("invalid_entity_id")
    if data["entity_type"] not in ENTITY_TYPES:
        raise ValueError("invalid_entity_type")
    for field, maximum in (("display_name", 120), ("issuer", 200)):
        value = data[field]
        if not isinstance(value, str) or not value.strip() or len(value) > maximum:
            raise ValueError(f"invalid_{field}")
    if data["status"] not in ENTITY_STATUSES:
        raise ValueError("invalid_entity_status")
    for field in ("created_at", "updated_at"):
        if not isinstance(data[field], str):
            raise ValueError(f"invalid_{field}")
        try:
            datetime.fromisoformat(data[field].replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid_{field}") from exc

    owner = _object(data["owner"], "owner")
    if not isinstance(owner.get("subject"), str) or not owner["subject"].strip():
        raise ValueError("invalid_owner_subject")

    for field in ("protocols", "capabilities", "permission_requests"):
        if not isinstance(data[field], list):
            raise ValueError(f"{field}_must_be_array")
    for protocol in data["protocols"]:
        item = _object(protocol, "protocol")
        if not isinstance(item.get("id"), str) or not item["id"].strip():
            raise ValueError("invalid_protocol_id")
        if not isinstance(item.get("version"), str) or not SEMVER.fullmatch(item["version"]):
            raise ValueError("invalid_protocol_version")

    for capability in data["capabilities"]:
        item = _object(capability, "capability")
        for field in ("capability_id", "version", "purpose"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"invalid_capability_{field}")
        if item.get("status") not in CAPABILITY_STATUSES:
            raise ValueError("invalid_capability_status")
        if not isinstance(item.get("evidence_refs"), list):
            raise ValueError("capability_evidence_refs_must_be_array")
        if not isinstance(item.get("required_scopes"), list):
            raise ValueError("capability_required_scopes_must_be_array")

    for request in data["permission_requests"]:
        item = _object(request, "permission_request")
        if not isinstance(item.get("action"), str) or not item["action"].strip():
            raise ValueError("invalid_permission_action")
        if not isinstance(item.get("resource_scope"), str) or not item["resource_scope"].strip():
            raise ValueError("invalid_permission_resource_scope")

    handling = _object(data["data_handling"], "data_handling")
    if not isinstance(handling.get("memory_classes"), list):
        raise ValueError("invalid_memory_classes")
    if not isinstance(handling.get("retention_policy"), str) or not handling["retention_policy"].strip():
        raise ValueError("invalid_retention_policy")

    _no_secret_fields(data)
    try:
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        json.loads(canonical)
    except (TypeError, ValueError) as exc:
        raise ValueError("manifest_not_json_serializable") from exc
    return data


class DigitalDNARegistry:
    """SQLite registry with workspace isolation and append-only manifest revisions."""

    def __init__(self, db_path: str = ".xparallel/digital_dna.sqlite3"):
        if db_path != ":memory:":
            Path(db_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(db_path, timeout=10, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS digital_dna_revisions (
                workspace_id TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                revision INTEGER NOT NULL,
                manifest_json TEXT NOT NULL,
                manifest_digest TEXT NOT NULL,
                recorded_at TEXT NOT NULL,
                PRIMARY KEY (workspace_id, entity_id, revision),
                UNIQUE (workspace_id, entity_id, manifest_digest)
            )
        """)
        self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_digital_dna_workspace
            ON digital_dna_revisions(workspace_id, entity_id, revision DESC)
        """)
        self._db.commit()

    @staticmethod
    def _record(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "workspace_id": row["workspace_id"],
            "entity_id": row["entity_id"],
            "revision": row["revision"],
            "manifest": json.loads(row["manifest_json"]),
            "manifest_digest": row["manifest_digest"],
            "recorded_at": row["recorded_at"],
        }

    def _latest_row(self, workspace_id: str, entity_id: str) -> sqlite3.Row | None:
        return self._db.execute(
            """SELECT * FROM digital_dna_revisions
               WHERE workspace_id=? AND entity_id=?
               ORDER BY revision DESC LIMIT 1""",
            (workspace_id, entity_id),
        ).fetchone()

    def register(self, workspace_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
        workspace = _workspace(workspace_id)
        data = validate_manifest(manifest)
        entity_id = data["entity_id"]
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with _LOCK, self._db:
            if self._latest_row(workspace, entity_id):
                raise ValueError("entity_already_registered")
            self._db.execute(
                """INSERT INTO digital_dna_revisions
                   (workspace_id, entity_id, revision, manifest_json, manifest_digest, recorded_at)
                   VALUES (?, ?, 1, ?, ?, ?)""",
                (workspace, entity_id, canonical, digest, _now()),
            )
            row = self._latest_row(workspace, entity_id)
            return self._record(row)

    def revise(
        self, workspace_id: str, entity_id: str, manifest: dict[str, Any],
        expected_revision: int,
    ) -> dict[str, Any]:
        workspace = _workspace(workspace_id)
        data = validate_manifest(manifest)
        if data["entity_id"] != entity_id:
            raise ValueError("entity_id_immutable")
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with _LOCK, self._db:
            current = self._latest_row(workspace, entity_id)
            if current is None:
                raise ValueError("entity_not_found")
            if current["revision"] != expected_revision:
                raise ValueError("revision_conflict")
            old_manifest = json.loads(current["manifest_json"])
            if data["owner"]["subject"] != old_manifest["owner"]["subject"]:
                raise ValueError("owner_transfer_requires_separate_verified_flow")
            if digest == current["manifest_digest"]:
                raise ValueError("manifest_unchanged")
            revision = current["revision"] + 1
            self._db.execute(
                """INSERT INTO digital_dna_revisions
                   (workspace_id, entity_id, revision, manifest_json, manifest_digest, recorded_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (workspace, entity_id, revision, canonical, digest, _now()),
            )
            return self._record(self._latest_row(workspace, entity_id))

    def get(self, workspace_id: str, entity_id: str, revision: int | None = None) -> dict[str, Any] | None:
        workspace = _workspace(workspace_id)
        with _LOCK:
            if revision is None:
                row = self._latest_row(workspace, entity_id)
            else:
                row = self._db.execute(
                    """SELECT * FROM digital_dna_revisions
                       WHERE workspace_id=? AND entity_id=? AND revision=?""",
                    (workspace, entity_id, int(revision)),
                ).fetchone()
            return self._record(row) if row else None

    def list(self, workspace_id: str, limit: int = 100) -> list[dict[str, Any]]:
        workspace = _workspace(workspace_id)
        bounded = max(1, min(int(limit), 500))
        with _LOCK:
            rows = self._db.execute(
                """SELECT r.* FROM digital_dna_revisions r
                   JOIN (
                     SELECT entity_id, MAX(revision) AS revision
                     FROM digital_dna_revisions WHERE workspace_id=?
                     GROUP BY entity_id
                   ) latest
                   ON latest.entity_id=r.entity_id AND latest.revision=r.revision
                   WHERE r.workspace_id=? ORDER BY r.recorded_at DESC LIMIT ?""",
                (workspace, workspace, bounded),
            ).fetchall()
            return [self._record(row) for row in rows]

    def close(self) -> None:
        with _LOCK:
            self._db.close()
