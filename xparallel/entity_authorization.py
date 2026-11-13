"""Deny-by-default policy evaluation for XParallel entity actions.

This is a policy primitive, not an authentication system or API middleware.
The caller must supply identity claims from a trusted server-side verifier,
never from an untrusted request body. No permissions are inferred from a
valid key signature or from a manifest's self-declared capability.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Iterable


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def authorize_entity_action(
    identity: dict[str, Any],
    grants: Iterable[dict[str, Any]],
    *,
    action: str,
    resource_scope: str,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Evaluate one action using trusted identity context and explicit grants.

    Required identity fields:
      authenticated: bool, workspace_id, subject, entity_id, owner_subject,
      entity_status='active', key_status='active', key_id,
      capability_status='verified', capability_id

    A grant must explicitly match workspace, entity, subject, key, capability,
    action, and exact resource scope; have status='approved'; and have a
    future expires_at timestamp. Wildcard/prefix scopes are intentionally
    unsupported.
    """
    decision = {"allowed": False, "reason": "deny_by_default"}
    if not isinstance(identity, dict):
        decision["reason"] = "identity_context_missing"
        return decision
    required = ("workspace_id", "subject", "entity_id", "owner_subject",
                "entity_status", "key_status", "key_id",
                "capability_status", "capability_id")
    if identity.get("authenticated") is not True:
        decision["reason"] = "caller_not_authenticated"
        return decision
    if any(not isinstance(identity.get(k), str) or not identity[k].strip() for k in required):
        decision["reason"] = "identity_context_incomplete"
        return decision
    if identity["subject"] != identity["owner_subject"]:
        decision["reason"] = "owner_subject_mismatch"
        return decision
    if identity["entity_status"] != "active":
        decision["reason"] = "entity_not_active"
        return decision
    if identity["key_status"] != "active":
        decision["reason"] = "signing_key_not_active"
        return decision
    if identity["capability_status"] != "verified":
        decision["reason"] = "capability_not_verified"
        return decision
    if not isinstance(action, str) or not action.strip() or not isinstance(resource_scope, str) or not resource_scope.strip():
        decision["reason"] = "invalid_action_or_scope"
        return decision

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        decision["reason"] = "invalid_policy_clock"
        return decision
    current = current.astimezone(timezone.utc)
    for grant in grants:
        if not isinstance(grant, dict):
            continue
        expected = {
            "workspace_id": identity["workspace_id"],
            "entity_id": identity["entity_id"],
            "subject": identity["subject"],
            "key_id": identity["key_id"],
            "capability_id": identity["capability_id"],
            "action": action,
            "resource_scope": resource_scope,
            "status": "approved",
        }
        if any(grant.get(key) != value for key, value in expected.items()):
            continue
        expires = _parse_time(grant.get("expires_at"))
        if expires is None or expires <= current:
            continue
        decision.update({
            "allowed": True,
            "reason": "explicit_grant_matched",
            "grant_id": grant.get("grant_id"),
            "expires_at": grant["expires_at"],
        })
        return decision
    decision["reason"] = "no_matching_unexpired_grant"
    return decision
