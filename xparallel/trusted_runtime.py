"""Trusted host identity adapter for XParallel runtime boundaries.

The host supplies an opaque session/credential to an injected authenticator.
Only authenticated server-side claims establish subject and workspace. Request
body/query actor or workspace fields are never identity evidence.

This module is an integration seam; it is not itself an authentication provider
and is not wired to the HTTP server until a real host verifier is configured.
"""
from __future__ import annotations

import re
from typing import Any, Callable

_WORKSPACE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


class TrustedRuntimeContext:
    """Resolve an opaque host session into a minimal, fail-closed principal."""

    def __init__(self, authenticate: Callable[[Any], dict[str, Any]]):
        if not callable(authenticate):
            raise TypeError("trusted_authenticator_required")
        self._authenticate = authenticate

    def resolve(
        self, session: Any, *, requested_workspace: str | None = None
    ) -> dict[str, str]:
        """Return trusted principal; optional requested workspace must match.

        requested_workspace is only a consistency check, never a source of
        authority. The returned workspace always comes from authenticated
        host claims.
        """
        try:
            claims = self._authenticate(session)
        except Exception as exc:
            raise PermissionError("trusted_authentication_failed") from exc
        if not isinstance(claims, dict) or claims.get("authenticated") is not True:
            raise PermissionError("caller_not_authenticated")

        subject = claims.get("subject")
        workspace = claims.get("workspace_id")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 256:
            raise PermissionError("trusted_subject_missing")
        if not isinstance(workspace, str) or not _WORKSPACE.fullmatch(workspace):
            raise PermissionError("trusted_workspace_invalid")
        if requested_workspace is not None:
            if not isinstance(requested_workspace, str) or requested_workspace != workspace:
                raise PermissionError("workspace_claim_mismatch")

        return {
            "authenticated": "true",
            "subject": subject.strip(),
            "workspace_id": workspace,
            "actor": subject.strip(),
        }
