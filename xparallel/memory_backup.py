"""Local backup and integrity-checked restore for the XParallel Memory Vault.

Backups are SQLite snapshots plus SHA-256 manifests. Configure XP_MEMORY_BACKUP_DIR
to a durable, access-controlled directory. This is not off-site or encrypted backup.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from xparallel.memory_vault import DEFAULT_DB, _connect

BACKUP_DIR = os.getenv("XP_MEMORY_BACKUP_DIR", "xparallel_memory_backups")
_BACKUP_ID = re.compile(r"^[0-9]{8}T[0-9]{6}Z-[0-9a-f]{12}$")


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _paths(backup_id: str, backup_dir: str | None = None) -> tuple[Path, Path]:
    if not _BACKUP_ID.fullmatch(str(backup_id)):
        raise ValueError("invalid_backup_id")
    root = Path(backup_dir or BACKUP_DIR).expanduser().resolve()
    return root / f"{backup_id}.sqlite3", root / f"{backup_id}.json"


def create_backup(db_path: str | None = None, backup_dir: str | None = None) -> dict[str, Any]:
    source_path = Path(db_path or DEFAULT_DB).expanduser().resolve()
    if not source_path.exists():
        # Initialize an empty, valid vault using the same schema as the live vault.
        with _connect(str(source_path)):
            pass
    root = Path(backup_dir or BACKUP_DIR).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    backup_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:12]
    backup_path, manifest_path = _paths(backup_id, str(root))
    temporary = backup_path.with_suffix(".sqlite3.tmp")
    source = sqlite3.connect(str(source_path), timeout=10)
    target = sqlite3.connect(str(temporary), timeout=10)
    try:
        source.backup(target)
        target.commit()
    finally:
        target.close()
        source.close()
    digest = _digest(temporary)
    os.replace(temporary, backup_path)
    manifest = {
        "backup_id": backup_id,
        "sha256": digest,
        "size_bytes": backup_path.stat().st_size,
        "created_at": time.time(),
        "source_db_name": source_path.name,
        "format": "sqlite3",
    }
    manifest_tmp = manifest_path.with_suffix(".json.tmp")
    manifest_tmp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(manifest_tmp, manifest_path)
    return {**manifest, "verified": True}


def verify_backup(backup_id: str, backup_dir: str | None = None) -> dict[str, Any]:
    backup_path, manifest_path = _paths(backup_id, backup_dir)
    if not backup_path.is_file() or not manifest_path.is_file():
        raise FileNotFoundError("backup_not_found")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    actual = _digest(backup_path)
    if manifest.get("backup_id") != backup_id or manifest.get("sha256") != actual:
        raise ValueError("backup_integrity_check_failed")
    # Confirm that SQLite can open and read the snapshot before marking it valid.
    connection = sqlite3.connect(f"file:{backup_path.as_posix()}?mode=ro", uri=True)
    try:
        result = connection.execute("PRAGMA quick_check").fetchone()
        if not result or result[0] != "ok":
            raise ValueError("backup_sqlite_check_failed")
    finally:
        connection.close()
    return {**manifest, "verified": True}


def list_backups(backup_dir: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    root = Path(backup_dir or BACKUP_DIR).expanduser().resolve()
    if not root.exists():
        return []
    limit = max(1, min(int(limit), 100))
    items = []
    for manifest_path in sorted(root.glob("*.json"), reverse=True):
        backup_id = manifest_path.stem
        try:
            items.append(verify_backup(backup_id, str(root)))
        except (ValueError, OSError, json.JSONDecodeError, sqlite3.Error):
            items.append({"backup_id": backup_id, "verified": False})
        if len(items) >= limit:
            break
    return items


def restore_backup(backup_id: str, db_path: str | None = None,
                   backup_dir: str | None = None) -> dict[str, Any]:
    """Restore a verified snapshot into the configured database, preserving a pre-restore copy."""
    verified = verify_backup(backup_id, backup_dir)
    target_path = Path(db_path or DEFAULT_DB).expanduser().resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    safety_copy = create_backup(str(target_path), backup_dir) if target_path.exists() else None
    source_path, _ = _paths(backup_id, backup_dir)
    temporary = target_path.with_name(target_path.name + ".restore-" + uuid.uuid4().hex)
    source = sqlite3.connect(f"file:{source_path.as_posix()}?mode=ro", uri=True)
    target = sqlite3.connect(str(temporary), timeout=10)
    try:
        source.backup(target)
        target.commit()
        check = target.execute("PRAGMA quick_check").fetchone()
        if not check or check[0] != "ok":
            raise ValueError("restore_sqlite_check_failed")
    finally:
        target.close()
        source.close()
    os.replace(temporary, target_path)
    return {"restored": True, "backup_id": backup_id, "sha256": verified["sha256"],
            "pre_restore_backup_id": safety_copy["backup_id"] if safety_copy else None}
