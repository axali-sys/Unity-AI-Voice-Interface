"""Composition gate joining trusted identity, verification evidence, grants and action policy.

This is an application-layer decision primitive. It does not execute actions and
must be called immediately before any separately controlled execution boundary.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from xparallel.capability_verification import CapabilityVerificationLab
from xparallel.entity_authorization import authorize_entity_action


class VerifiedEntityActionGate:
    """Fail-closed composition of identity, capability evidence and permission.

    resolve_entity_context(principal, entity_id, key_id, capability_id) must
    return trusted server-side fields: owner_subject, entity_status, key_status,
    capability_version, artifact_digest. It must not trust request-body claims.

    load_active_grants(principal, entity_id) must return only authoritative
    approved grants for the principal's workspace/entity. It must not accept
    grants supplied by the client.
    """

    def __init__(
        self,
        *,
        authenticate: Callable[[Any], dict[str, Any]],
        resolve_entity_context: Callable[[dict[str, str], str, str, str], dict[str, Any]],
        load_active_grants: Callable[[dict[str, str], str], list[dict[str, Any]]],
        verification_lab: CapabilityVerificationLab,
    ):
        if not all(callable(x) for x in (authenticate, resolve_entity_context, load_active_grants)):
            raise TypeError("trusted_action_gate_adapters_required")
        if not isinstance(verification_lab, CapabilityVerificationLab):
            raise TypeError("capability_verification_lab_required")
        self._authenticate = authenticate
        self._resolve = resolve_entity_context
        self._load_grants = load_active_grants
        self._lab = verification_lab

    def authorize(
        self,
        session: Any,
        *,
        entity_id: str,
        key_id: str,
        capability_id: str,
        action: str,
        resource_scope: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        denied = {"allowed": False, "reason": "deny_by_default"}
        try:
            principal_raw = self._authenticate(session)
            if not isinstance(principal_raw, dict) or principal_raw.get("authenticated") is not True:
                return {**denied, "reason": "caller_not_authenticated"}
            subject = principal_raw.get("subject")
            workspace = principal_raw.get("workspace_id")
            if not isinstance(subject, str) or not subject.strip() or not isinstance(workspace, str) or not workspace.strip():
                return {**denied, "reason": "trusted_principal_incomplete"}
            principal = {"authenticated": True, "subject": subject, "workspace_id": workspace}
            context = self._resolve(principal, entity_id, key_id, capability_id)
            if not isinstance(context, dict):
                return {**denied, "reason": "trusted_entity_context_missing"}
            version = context.get("capability_version")
            digest = context.get("artifact_digest")
            if not isinstance(version, str) or not version or not isinstance(digest, str) or not digest:
                return {**denied, "reason": "capability_artifact_binding_missing"}
            evidence = self._lab.status(
                workspace, entity_id, capability_id, version, digest, now=now
            )
            identity = {
                **principal,
                "entity_id": entity_id,
                "key_id": key_id,
                "capability_id": capability_id,
                "owner_subject": context.get("owner_subject"),
                "entity_status": context.get("entity_status"),
                "key_status": context.get("key_status"),
                "capability_status": evidence.get("status"),
            }
            grants = self._load_grants(principal, entity_id)
            if not isinstance(grants, list):
                return {**denied, "reason": "trusted_grant_repository_unavailable"}
            decision = authorize_entity_action(
                identity, grants, action=action, resource_scope=resource_scope, now=now
            )
            decision["capability_evidence"] = {
                "status": evidence.get("status"),
                "reason": evidence.get("reason"),
                "run_id": evidence.get("run_id"),
                "expires_at": evidence.get("expires_at"),
            }
            return decision
        except Exception:
            # Dependency failure, malformed trusted state, or storage outage must
            # never turn into an authorization success.
            return {**denied, "reason": "authorization_dependency_failure"}

