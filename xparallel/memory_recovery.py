"""Fail-closed workspace memory recovery from verified local snapshots.

Recovery never accepts a caller-supplied snapshot payload. It reads the immutable
snapshot record, verifies its manifest and each source-content digest, then uses
one SQLite transaction to merge or replace the selected destination workspace.
"""
from __future__ import annotations

import json
from typing import Any

from .memory_backup import verify_snapshot, _ensure_schema
from .memory_vault import _connect


def recover_snapshot(snapshot_id: str, source_workspace: str,
                     target_workspace: str | None = None, *,
                     mode: str = "merge", authorized: bool = False,
                     explicit_scope: bool = False,
                     db_path: str | None = None) -> dict[str, Any]:
    source = str(source_workspace or "default").strip()[:200] or "default"
    target = str(target_workspace if target_workspace is not None else source).strip()[:200] or "default"

    if mode not in {"merge", "replace"}:
        return {"recovered": False, "reason": "invalid_recovery_mode"}
    if not authorized or not explicit_scope:
        return {"recovered": False, "reason": "recovery_requires_authorization_and_scope"}
    if source != target and not authorized:
        return {"recovered": False, "reason": "cross_workspace_recovery_denied"}

    verification = verify_snapshot(snapshot_id, source, db_path)
    if not verification.get("valid"):
        return {"recovered": False, "reason": verification.get("reason", "snapshot_invalid")}

    payload = verification["payload"]
    items = payload["items"]
    with _connect(db_path) as conn:
        _ensure_schema(conn)
        # Explicitly re-read and verify inside the write transaction to narrow
        # the time-of-check/time-of-use window.
        row = conn.execute(
            "SELECT payload_json,payload_sha256 FROM memory_snapshots "
            "WHERE snapshot_id=? AND workspace_id=?", (str(snapshot_id), source)
        ).fetchone()
        if not row or row["payload_json"] != json.dumps(
                payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")):
            return {"recovered": False, "reason": "snapshot_changed"}
        if mode == "merge":
            # Reject reused IDs with different content before mutating anything.
            for item in items:
                existing = conn.execute(
                    "SELECT content_hash FROM memory_items WHERE id=? AND workspace_id=?",
                    (item["id"], target)
                ).fetchone()
                if existing and existing["content_hash"] != item["content_hash"]:
                    return {"recovered": False, "reason": "target_memory_id_conflict"}

        if mode == "replace":
            conn.execute("DELETE FROM memory_items WHERE workspace_id=?", (target,))

        restored = 0
        for item in items:
            # The snapshot's owner remains the source identity; destination
            # workspace is set only by this explicitly authorized operation.
            conn.execute(
                "INSERT OR IGNORE INTO memory_items"
                "(id,workspace_id,content_hash,content,summary,tags_json,created_at,updated_at) "
                "VALUES(?,?,?,?,?,?,?,?)",
                (item["id"], target, item["content_hash"], item["content"],
                 item.get("summary", ""), json.dumps(item.get("tags", [])),
                 item["created_at"], item["updated_at"]),
            )
            restored += conn.execute("SELECT changes()").fetchone()[0]
    return {
        "recovered": True, "snapshot_id": str(snapshot_id),
        "source_workspace": source, "target_workspace": target,
        "mode": mode, "restored_count": restored,
        "snapshot_item_count": len(items), "integrity_verified": True,
    }
