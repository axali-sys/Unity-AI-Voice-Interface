"""Transactional local SQLite storage, migrations, backup and recovery helpers.

This is a development backend/reference repository layer. It does not claim
distributed durability, encryption, immutable audit, or production HA.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator
from urllib.parse import quote

_LOCK = threading.RLock()


@dataclass(frozen=True)
class Migration:
    version: int
    statements: tuple[str, ...]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class SQLiteStore:
    """Single-process transactional SQLite store with explicit recovery controls."""

    def __init__(
        self, path: str, *,
        authorize_restore: Callable[[Any], bool],
        timeout_seconds: float = 10.0,
    ):
        if not callable(authorize_restore):
            raise TypeError("restore_authorization_adapter_required")
        if not isinstance(timeout_seconds, (int, float)) or not 1 <= timeout_seconds <= 60:
            raise ValueError("sqlite_timeout_out_of_range")
        self.path = str(Path(path).expanduser().resolve()) if path != ":memory:" else path
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._authorize_restore = authorize_restore
        self._timeout = float(timeout_seconds)
        self._db = sqlite3.connect(self.path, timeout=self._timeout, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("PRAGMA synchronous=FULL")
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY, checksum TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        self._db.commit()

    @staticmethod
    def _migration_checksum(migration: Migration) -> str:
        if not isinstance(migration, Migration) or not isinstance(migration.version, int) or migration.version < 1:
            raise ValueError("invalid_migration")
        if not migration.statements or any(not isinstance(s, str) or not s.strip() for s in migration.statements):
            raise ValueError("migration_statements_required")
        return hashlib.sha256(_canonical(list(migration.statements)).encode("utf-8")).hexdigest()

    def apply_migrations(self, migrations: list[Migration]) -> int:
        if not isinstance(migrations, list):
            raise ValueError("migrations_must_be_list")
        normalized = sorted(migrations, key=lambda m: m.version)
        if len({m.version for m in normalized}) != len(normalized):
            raise ValueError("duplicate_migration_version")
        applied_count = 0
        with _LOCK:
            for migration in normalized:
                checksum = self._migration_checksum(migration)
                existing = self._db.execute(
                    "SELECT checksum FROM schema_migrations WHERE version=?",
                    (migration.version,),
                ).fetchone()
                if existing:
                    if existing["checksum"] != checksum:
                        raise ValueError("applied_migration_checksum_changed")
                    continue
                latest = self._db.execute(
                    "SELECT COALESCE(MAX(version), 0) AS version FROM schema_migrations"
                ).fetchone()["version"]
                if migration.version != latest + 1:
                    raise ValueError("migration_sequence_gap")
                with self._db:
                    for statement in migration.statements:
                        self._db.execute(statement)
                    self._db.execute(
                        "INSERT INTO schema_migrations(version, checksum, applied_at) VALUES (?, ?, ?)",
                        (migration.version, checksum, datetime.now(timezone.utc).isoformat()),
                    )
                applied_count += 1
        return applied_count

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with _LOCK:
            self._db.execute("BEGIN IMMEDIATE")
            try:
                yield self._db
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def backup(self, destination: str) -> dict[str, Any]:
        target_path = Path(destination).expanduser().resolve()
        if self.path == ":memory:" or target_path == Path(self.path):
            raise ValueError("invalid_backup_destination")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            raise FileExistsError("backup_destination_already_exists")
        target = None
        try:
            with _LOCK:
                target = sqlite3.connect(str(target_path))
                self._db.backup(target)
                target.commit()
                result = target.execute("PRAGMA integrity_check").fetchone()[0]
                if result != "ok":
                    raise sqlite3.DatabaseError("backup_integrity_check_failed")
                target.close()
                target = None
            return {"path": str(target_path), "integrity": result,
                    "size_bytes": target_path.stat().st_size}
        except Exception:
            if target is not None:
                target.close()
            target_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def verify_database(path: str) -> dict[str, Any]:
        target = Path(path).expanduser().resolve()
        if not target.is_file():
            raise FileNotFoundError("database_file_not_found")
        uri = "file:" + quote(str(target)) + "?mode=ro"
        db = sqlite3.connect(uri, uri=True)
        try:
            integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                return {"valid": False, "integrity": integrity}
            try:
                version = db.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
                ).fetchone()[0]
            except sqlite3.OperationalError:
                version = 0
            return {"valid": True, "integrity": integrity, "schema_version": version}
        finally:
            db.close()

    def restore_from(self, source: str, approval: Any) -> dict[str, Any]:
        source_path = Path(source).expanduser().resolve()
        if self.path == ":memory:" or source_path == Path(self.path) or not source_path.is_file():
            raise ValueError("invalid_restore_source")
        if self._authorize_restore(approval) is not True:
            raise PermissionError("restore_not_authorized")
        source_status = self.verify_database(str(source_path))
        if not source_status["valid"]:
            raise sqlite3.DatabaseError("restore_source_integrity_failed")
        current_version = self._db.execute(
            "SELECT COALESCE(MAX(version), 0) FROM schema_migrations"
        ).fetchone()[0]
        if source_status["schema_version"] != current_version:
            raise ValueError("restore_schema_version_mismatch")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        safety_path = self.path + ".pre-restore-" + stamp + ".sqlite3"
        safety = self.backup(safety_path)
        source_db = sqlite3.connect("file:" + quote(str(source_path)) + "?mode=ro", uri=True)
        try:
            with _LOCK:
                source_db.backup(self._db)
                self._db.commit()
                integrity = self._db.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise sqlite3.DatabaseError("restored_database_integrity_failed")
        except Exception:
            safety_db = sqlite3.connect(safety_path)
            try:
                safety_db.backup(self._db)
                self._db.commit()
            finally:
                safety_db.close()
            raise
        finally:
            source_db.close()
        return {"restored": True, "integrity": integrity,
                "safety_backup": safety["path"], "schema_version": current_version}

    @staticmethod
    def prune_backups(directory: str, *, prefix: str, keep: int = 5) -> dict[str, Any]:
        root = Path(directory).expanduser().resolve()
        if not root.is_dir():
            raise NotADirectoryError("backup_directory_not_found")
        if not isinstance(prefix, str) or not prefix or Path(prefix).name != prefix:
            raise ValueError("invalid_backup_prefix")
        if not isinstance(keep, int) or isinstance(keep, bool) or keep < 1:
            raise ValueError("backup_retention_keep_must_be_positive")
        files = [
            path for path in root.iterdir()
            if path.is_file() and not path.is_symlink()
            and path.name.startswith(prefix) and path.name.endswith(".sqlite3")
        ]
        files.sort(key=lambda p: (p.stat().st_mtime_ns, p.name), reverse=True)
        removed = []
        for path in files[keep:]:
            path.unlink()
            removed.append(path.name)
        return {"kept": [p.name for p in files[:keep]], "removed": removed}

    def close(self) -> None:
        with _LOCK:
            self._db.close()


class SQLiteJSONRepository:
    """Workspace-scoped JSON record repository over SQLiteStore."""

    def __init__(self, store: SQLiteStore, *, table: str = "workspace_records"):
        if not isinstance(store, SQLiteStore):
            raise TypeError("sqlite_store_required")
        if not isinstance(table, str) or not table.replace("_", "").isalnum() or not table[0].isalpha():
            raise ValueError("invalid_repository_table")
        self._store = store
        self._table = table
        store.apply_migrations([Migration(1, (
            f"""CREATE TABLE IF NOT EXISTS {table} (
                workspace_id TEXT NOT NULL, record_key TEXT NOT NULL,
                value_json TEXT NOT NULL, updated_at TEXT NOT NULL,
                PRIMARY KEY(workspace_id, record_key)
            )""",
        ))])

    def put(self, workspace_id: str, key: str, value: Any) -> dict[str, Any]:
        if not isinstance(workspace_id, str) or not workspace_id.strip() or len(workspace_id) > 200:
            raise ValueError("invalid_workspace_id")
        if not isinstance(key, str) or not key.strip() or len(key) > 200:
            raise ValueError("invalid_record_key")
        canonical = _canonical(value)
        now = datetime.now(timezone.utc).isoformat()
        with self._store.transaction() as db:
            db.execute(
                f"""INSERT INTO {self._table}(workspace_id, record_key, value_json, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(workspace_id, record_key) DO UPDATE SET
                    value_json=excluded.value_json, updated_at=excluded.updated_at""",
                (workspace_id, key, canonical, now),
            )
        return {"workspace_id": workspace_id, "key": key, "updated_at": now}

    def get(self, workspace_id: str, key: str) -> Any | None:
        with _LOCK:
            row = self._store._db.execute(
                f"SELECT value_json FROM {self._table} WHERE workspace_id=? AND record_key=?",
                (workspace_id, key),
            ).fetchone()
        return json.loads(row["value_json"]) if row else None

    def list(self, workspace_id: str, limit: int = 100) -> list[dict[str, Any]]:
        bounded = max(1, min(int(limit), 500))
        with _LOCK:
            rows = self._store._db.execute(
                f"""SELECT record_key, value_json, updated_at FROM {self._table}
                    WHERE workspace_id=? ORDER BY updated_at DESC LIMIT ?""",
                (workspace_id, bounded),
            ).fetchall()
        return [{"key": row["record_key"], "value": json.loads(row["value_json"]),
                 "updated_at": row["updated_at"]} for row in rows]
