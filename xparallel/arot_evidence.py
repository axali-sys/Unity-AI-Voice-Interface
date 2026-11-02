"""AROT evidence adapter over the existing audit repository."""
from __future__ import annotations
from xparallel.audit_repository import AUDIT_REPOSITORY

def record_event(event_type, workspace_id, actor_id, entity_id, payload=None):
    """Persist a traceable AROT event using the existing audit ledger."""
    return AUDIT_REPOSITORY.record(
        "arot:" + str(event_type)[:100],
        str(workspace_id),
        str(actor_id or "system"),
        {"entity_id": str(entity_id), "event_type": str(event_type),
         "evidence": payload if isinstance(payload, dict) else {}},
    )

def record_task_event(task, event_type, actor_id, payload=None):
    return record_event(event_type, task["workspace_id"], actor_id, task["id"], payload)
