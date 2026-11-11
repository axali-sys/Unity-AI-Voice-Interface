"""Signed enterprise identity context for tenant-scoped API adapters.

This module verifies short-lived HS256 bearer claims issued only after an upstream
login provider has authenticated the human. XP_TOKEN is a service credential and
must never be treated as an end-user identity token.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any


class IdentityError(ValueError):
    """Raised when an enterprise identity token is absent or invalid."""


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    if not isinstance(value, str) or len(value) > 8192:
        raise IdentityError("invalid_identity_token")
    try:
        return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
    except Exception as exc:
        raise IdentityError("invalid_identity_token") from exc


def _secret(secret: str | None = None) -> bytes:
    value = (secret if secret is not None else os.getenv("XP_IDENTITY_SIGNING_SECRET", "")).encode()
    if len(value) < 32:
        raise IdentityError("identity_signing_not_configured")
    return value


def issue_identity_token(*, subject: str, workspace_id: str, role: str,
                         secret: str | None = None, ttl_seconds: int = 900,
                         now: int | None = None) -> str:
    """Issue claims for a trusted server-side auth adapter, never directly from browser input."""
    sub = str(subject or "").strip()
    workspace = str(workspace_id or "").strip()
    if not sub or len(sub) > 128 or not workspace or len(workspace) > 128:
        raise IdentityError("invalid_identity_claims")
    if not isinstance(role, str) or role not in {"owner", "admin", "operator", "viewer"}:
        raise IdentityError("invalid_identity_role")
    if not isinstance(ttl_seconds, int) or not 1 <= ttl_seconds <= 3600:
        raise IdentityError("invalid_identity_ttl")
    issued = int(time.time()) if now is None else int(now)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": sub, "workspace_id": workspace, "role": role,
               "iat": issued, "exp": issued + ttl_seconds}
    signing_input = _b64encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode()) + "." + _b64encode(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode())
    signature = hmac.new(_secret(secret), signing_input.encode(), hashlib.sha256).digest()
    return signing_input + "." + _b64encode(signature)


def verify_identity_token(token: str, *, secret: str | None = None,
                          now: int | None = None) -> dict[str, Any]:
    """Verify signature, algorithm, expiry and bounded identity claims."""
    if not isinstance(token, str) or len(token) > 16384:
        raise IdentityError("invalid_identity_token")
    parts = token.split(".")
    if len(parts) != 3:
        raise IdentityError("invalid_identity_token")
    header_raw, payload_raw, signature_raw = parts
    try:
        header = json.loads(_b64decode(header_raw))
        claims = json.loads(_b64decode(payload_raw))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise IdentityError("invalid_identity_token") from exc
    if not isinstance(header, dict) or header.get("alg") != "HS256" or header.get("typ") != "JWT":
        raise IdentityError("invalid_identity_algorithm")
    signing_input = header_raw + "." + payload_raw
    expected = hmac.new(_secret(secret), signing_input.encode(), hashlib.sha256).digest()
    supplied = _b64decode(signature_raw)
    if not hmac.compare_digest(expected, supplied):
        raise IdentityError("invalid_identity_signature")
    if not isinstance(claims, dict):
        raise IdentityError("invalid_identity_claims")
    current = int(time.time()) if now is None else int(now)
    try:
        issued, expires = int(claims["iat"]), int(claims["exp"])
        subject = str(claims["sub"]).strip()
        workspace = str(claims["workspace_id"]).strip()
        role = claims["role"]
    except (KeyError, TypeError, ValueError) as exc:
        raise IdentityError("invalid_identity_claims") from exc
    if not subject or len(subject) > 128 or not workspace or len(workspace) > 128:
        raise IdentityError("invalid_identity_claims")
    if not isinstance(role, str) or role not in {"owner", "admin", "operator", "viewer"}:
        raise IdentityError("invalid_identity_role")
    if issued > current + 30 or expires <= current or expires <= issued or expires - issued > 3600:
        raise IdentityError("identity_token_expired_or_invalid")
    return {"actor": subject, "workspace_id": workspace, "role": role,
            "issued_at": issued, "expires_at": expires}
