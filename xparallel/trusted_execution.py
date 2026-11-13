"""Trusted composition of entity authorization and execution approvals.

This module creates immutable execution intents only. It does not launch code.
All identity, artifact, grant, approval, cancellation, and executor decisions
must come from trusted host adapters.
"""
from __future__ import annotations

from typing import Any, Callable

from xparallel.execution_approval import ExecutionApprovalRegistry


class TrustedExecutionControlPlane:
    """Bind the verified action gate to one-time execution approval records."""

    def __init__(
        self,
        *,
        trusted_host: Any,
        authorize_approval: Callable[[dict[str, str], dict[str, Any]], bool],
        authorize_cancel: Callable[[dict[str, str], dict[str, Any]], bool],
        authorize_executor: Callable[[dict[str, str], dict[str, Any]], bool],
        db_path: str = ".xparallel/execution_approvals.sqlite3",
    ):
        for name, adapter in (
            ("authorize_approval", authorize_approval),
            ("authorize_cancel", authorize_cancel),
            ("authorize_executor", authorize_executor),
        ):
            if not callable(adapter):
                raise TypeError(f"{name}_adapter_required")
        for name in ("authenticate", "resolve_entity_context", "load_active_grants", "build_action_gate"):
            if not callable(getattr(trusted_host, name, None)):
                raise TypeError("trusted_host_adapter_incomplete")

        self._host = trusted_host
        # The registry authenticates the external session first. From this point
        # onward, internal callbacks receive only that normalized principal.
        self._gate = trusted_host.build_action_gate(
            authenticate=lambda principal: {"authenticated": True, **principal}
        )

        def current_state(principal: dict[str, str], intent: dict[str, Any], stage: str) -> bool:
            try:
                if intent.get("workspace_id") != principal.get("workspace_id"):
                    return False
                context = trusted_host.resolve_entity_context(
                    principal, intent["entity_id"], intent["key_id"], intent["capability_id"]
                )
                if not isinstance(context, dict):
                    return False
                if context.get("artifact_digest") != intent.get("artifact_digest"):
                    return False
                decision = self._gate.authorize(
                    principal,
                    entity_id=intent["entity_id"],
                    key_id=intent["key_id"],
                    capability_id=intent["capability_id"],
                    action=intent["action"],
                    resource_scope=intent["resource_scope"],
                )
                return decision.get("allowed") is True
            except Exception:
                return False

        def authorize_request(principal: dict[str, str], intent: dict[str, Any]) -> bool:
            return current_state(principal, intent, "request")

        self.approvals = ExecutionApprovalRegistry(
            authenticate=trusted_host.authenticate,
            authorize_request=authorize_request,
            authorize_approval=authorize_approval,
            authorize_cancel=authorize_cancel,
            authorize_executor=authorize_executor,
            validate_current_state=current_state,
            db_path=db_path,
        )

    def close(self) -> None:
        self.approvals.close()
