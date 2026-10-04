"""XParallel Solution Engine V1.

Turns a human outcome request into a deterministic solution record.
Execution remains separate and approval-gated.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any

ENGINE_VERSION = "1.0.0"
MAX_QUERY = 4000


def _slug(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:64] or "solution"


def _fingerprint(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(canonical).hexdigest()


def create_solution(query: str) -> dict[str, Any]:
    query = str(query).strip()
    if not query:
        raise ValueError("query_required")
    if len(query) > MAX_QUERY:
        raise ValueError("query_too_large")

    now = datetime.now(timezone.utc).isoformat()
    solution = {
        "engine": "XParallel Solution Engine",
        "engine_version": ENGINE_VERSION,
        "solution_id": f"xp-{_slug(query)[:32]}-{hashlib.sha256(query.encode()).hexdigest()[:12]}",
        "request": query,
        "lifecycle": [
            "INTAKE",
            "PLAN",
            "SANDBOX",
            "TEST",
            "EVIDENCE",
            "HUMAN_APPROVAL",
            "DEPLOY",
        ],
        "current_stage": "INTAKE",
        "execution_policy": "approval-gated",
        "created_at": now,
        "evidence": {
            "tests": [],
            "artifacts": [],
            "deployment": "not_authorized",
        },
    }
    solution["fingerprint"] = _fingerprint(solution)
    return solution


def verify_solution(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("solution_record_required")
    supplied = record.get("fingerprint")
    if not supplied:
        return {"verified": False, "reason": "fingerprint_missing"}
    copy = dict(record)
    copy.pop("fingerprint", None)
    expected = _fingerprint(copy)
    return {
        "verified": supplied == expected,
        "fingerprint": supplied,
        "expected_fingerprint": expected,
        "engine_version": ENGINE_VERSION,
    }
