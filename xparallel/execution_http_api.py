"""Private JWT-bound HTTP service for trusted XParallel execution.

This adapter is deliberately inert until a host explicitly constructs it with
a trusted control plane and fully configured execution host services.
"""
from __future__ import annotations

from typing import Any


class ExecutionHTTPAPI:
    """Expose execution operations using verified claims plus the original bearer token.

The HTTP layer validates claims for route roles. The approval registry receives
the original token so the configured trusted host authenticator independently
revalidates identity and workspace instead of trusting a caller-built dict.
"""

    def __init__(self, *, control_plane: Any, host_services: Any, recovery_supervisor: Any | None = None):
        approvals = getattr(control_plane, "approvals", None)
        if approvals is None or getattr(host_services, "approvals", None) is not approvals:
            raise TypeError("execution_control_plane_and_host_services_must_share_approval_registry")
        build_worker = getattr(host_services, "build_worker", None)
        if not callable(build_worker):
            raise TypeError("trusted_execution_host_services_required")
        self._approvals = approvals
        self._worker = build_worker()
        if recovery_supervisor is not None and not callable(getattr(recovery_supervisor, 'health', None)):
            raise TypeError('recovery_supervisor_health_adapter_required')
        self._recovery_supervisor = recovery_supervisor

    @staticmethod
    def _principal(claims: Any, roles: set[str]) -> dict[str, str]:
        if not isinstance(claims, dict) or claims.get("authenticated") is not True:
            raise PermissionError("trusted_jwt_identity_required")
        subject, workspace, role = claims.get("subject"), claims.get("workspace_id"), claims.get("role")
        if not isinstance(subject, str) or not subject.strip():
            raise PermissionError("trusted_subject_missing")
        if not isinstance(workspace, str) or not workspace.strip():
            raise PermissionError("trusted_workspace_missing")
        if role not in roles:
            raise PermissionError("execution_role_not_authorized")
        return {"subject": subject, "workspace_id": workspace, "role": role}

    @staticmethod
    def _session_token(token: Any) -> str:
        if not isinstance(token, str) or not token.strip():
            raise PermissionError("trusted_session_token_required")
        return token

    @staticmethod
    def _exact(data: Any, fields: set[str]) -> dict[str, Any]:
        if not isinstance(data, dict) or set(data) != fields:
            raise ValueError("execution_request_schema_mismatch")
        return data

    def request_intent(self, claims: Any, data: Any, *, session_token: Any) -> dict[str, Any]:
        principal = self._principal(claims, {"owner", "operator"})
        body = self._exact(data, {
            "entity_id", "key_id", "capability_id", "action", "resource_scope",
            "payload_digest", "artifact_digest", "runner_image_digest", "limits",
        })
        token = self._session_token(session_token)
        result = self._approvals.request_intent(token, **body)
        return {"intent": result}

    def approve_intent(self, claims: Any, data: Any, *, session_token: Any) -> dict[str, Any]:
        principal = self._principal(claims, {"owner", "admin"})
        body = self._exact(data, {"intent_id", "reason"})
        token = self._session_token(session_token)
        result = self._approvals.approve(token, body["intent_id"], reason=body["reason"])
        # The one-use ticket is returned only to the approving principal.
        return {"approval": result}

    def execute_ticket(self, claims: Any, data: Any, *, session_token: Any) -> dict[str, Any]:
        principal = self._principal(claims, {"operator"})
        body = self._exact(data, {"one_time_ticket"})
        if not isinstance(body["one_time_ticket"], str):
            raise ValueError("invalid_execution_ticket")
        token = self._session_token(session_token)
        return self._worker.execute(token, body["one_time_ticket"])

    def recover_pending(self, claims: Any, data: Any, *, session_token: Any) -> dict[str, Any]:
        principal = self._principal(claims, {"operator"})
        body = self._exact(data, {"limit"})
        token = self._session_token(session_token)
        return self._worker.recover_pending_finalizations(token, limit=body["limit"])

    def recovery_health(self, claims: Any) -> dict[str, Any]:
        """Return sanitized recovery health to an authenticated operator."""
        self._principal(claims, {"owner", "admin", "operator"})
        if self._recovery_supervisor is None:
            raise LookupError("execution_recovery_supervisor_not_configured")
        snapshot = self._recovery_supervisor.health()
        if not isinstance(snapshot, dict):
            raise RuntimeError("invalid_execution_recovery_health")
        return {"recovery": snapshot}
