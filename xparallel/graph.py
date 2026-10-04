"""Persistent-ready Solution Graph primitives for XParallel V1.

The graph is deliberately storage-agnostic so the first version can run without
forcing a database migration. A later adapter can persist the same records in
PostgreSQL or another enterprise datastore.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _key(record: dict[str, Any]) -> str:
    raw = json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


class SolutionGraph:
    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}

    def add(self, solution: dict[str, Any], *, status: str = "candidate", tags: list[str] | None = None) -> dict[str, Any]:
        if not isinstance(solution, dict) or not solution.get("solution_id"):
            raise ValueError("solution_record_required")
        record = {
            "graph_version": "1.0.0",
            "node_id": solution["solution_id"],
            "status": status,
            "tags": sorted(set(tags or [])),
            "solution": solution,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        record["graph_fingerprint"] = _key(record)
        self._records[record["node_id"]] = record
        return record

    def get(self, node_id: str) -> dict[str, Any] | None:
        return self._records.get(node_id)

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        terms = {term.lower() for term in str(query).split() if len(term) > 2}
        if not terms:
            return []
        scored = []
        for record in self._records.values():
            text = json.dumps(record["solution"], sort_keys=True).lower()
            score = sum(term in text for term in terms)
            if score:
                scored.append((score, record))
        scored.sort(key=lambda item: (-item[0], item[1]["created_at"]))
        return [record for _, record in scored[:max(1, min(limit, 50))]]

    def promote(self, node_id: str) -> dict[str, Any]:
        record = self._records.get(node_id)
        if not record:
            raise KeyError("solution_not_found")
        record["status"] = "verified"
        record["verified_at"] = datetime.now(timezone.utc).isoformat()
        record["graph_fingerprint"] = _key({k: v for k, v in record.items() if k != "graph_fingerprint"})
        return record

    def summary(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self._records.values():
            status = record["status"]
            counts[status] = counts.get(status, 0) + 1
        return {"total": len(self._records), **counts}


GRAPH = SolutionGraph()
