"""Short-lived, single-use, action-bound XParallel approval tickets."""
from __future__ import annotations
import hashlib
import json
import secrets
import threading
import time
from typing import Any

_TTL_SECONDS = 120
_TICKETS: dict[str, dict[str, Any]] = {}
_LOCK = threading.Lock()

def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def issue_approval(*, plugin_id: str, action: str, payload: dict[str, Any], workspace_id: str, actor: str) -> dict[str, Any]:
    """Mint a short-lived ticket after the server verifies an explicit approval credential."""
    now = time.time()
    ticket = secrets.token_urlsafe(32)
    record = {"plugin_id": plugin_id, "action": action, "payload_sha256": _payload_digest(payload),
              "workspace_id": workspace_id, "actor": actor, "expires_at": now + _TTL_SECONDS}
    with _LOCK:
        for key in [k for k, v in _TICKETS.items() if v["expires_at"] <= now]:
            _TICKETS.pop(key, None)
        _TICKETS[ticket] = record
    return {"approval_ticket": ticket, "expires_in_seconds": _TTL_SECONDS,
            "bound_to": {"plugin_id": plugin_id, "action": action, "workspace_id": workspace_id, "actor": actor}}

def consume_approval(ticket: str, *, plugin_id: str, action: str, payload: dict[str, Any], workspace_id: str, actor: str) -> bool:
    """Consume once; any mismatch or expiry rejects the approval."""
    if not isinstance(ticket, str) or not ticket:
        return False
    now = time.time()
    with _LOCK:
        record = _TICKETS.pop(ticket, None)
    if not record or record["expires_at"] <= now:
        return False
    return (record["plugin_id"] == plugin_id and record["action"] == action
            and secrets.compare_digest(record["payload_sha256"], _payload_digest(payload))
            and record["workspace_id"] == workspace_id and record["actor"] == actor)
