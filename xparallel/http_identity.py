"""HTTP identity binding helpers for trusted XParallel sessions."""
from __future__ import annotations

from typing import Any


class IdentityBindingError(PermissionError):
    """A request attempted to override authenticated identity or tenancy."""


def bearer_token(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    scheme, separator, token = value.partition(" ")
    if not separator or scheme.lower() != "bearer" or not token or " " in token:
        return None
    return token


def bind_request_identity(data: dict[str, Any], claims: dict[str, Any]) -> dict[str, Any]:
    """Bind workspace and actor from verified claims, rejecting caller overrides."""
    if not isinstance(data, dict) or not isinstance(claims, dict):
        raise IdentityBindingError("trusted_identity_required")
    subject = claims.get("subject")
    workspace = claims.get("workspace_id")
    role = claims.get("role", "viewer")
    if not isinstance(subject, str) or not subject.strip():
        raise IdentityBindingError("trusted_subject_missing")
    if not isinstance(workspace, str) or not workspace:
        raise IdentityBindingError("trusted_workspace_missing")
    if role not in {"owner", "admin", "operator", "viewer"}:
        raise IdentityBindingError("trusted_role_invalid")

    def one(value):
        if isinstance(value, list):
            if len(value) != 1:
                raise IdentityBindingError("ambiguous_identity_parameter")
            return value[0]
        return value

    requested_workspace = one(data.get("workspace_id"))
    if requested_workspace not in (None, "") and requested_workspace != workspace:
        raise IdentityBindingError("workspace_claim_mismatch")
    requested_actor = one(data.get("actor"))
    if requested_actor not in (None, "") and requested_actor != subject:
        raise IdentityBindingError("actor_claim_mismatch")

    bound = dict(data)
    bound["workspace_id"] = workspace
    bound["actor"] = subject
    return bound
