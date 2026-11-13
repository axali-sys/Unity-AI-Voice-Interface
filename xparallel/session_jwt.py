"""Dependency-free HS256 host-session verifier for XParallel.

This verifies signed host-issued JWTs. It does not issue tokens or establish
user identity itself; the host must authenticate the user and issue claims.
Use a high-entropy secret (at least 32 bytes), HTTPS, short expirations, and
separate secrets per environment. Never accept tokens from request JSON.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
from typing import Any

_B64URL = re.compile(r"^[A-Za-z0-9_-]+$")


def _decode_segment(segment: str) -> bytes:
    if not isinstance(segment, str) or not segment or not _B64URL.fullmatch(segment):
        raise ValueError("invalid_session_token_encoding")
    try:
        return base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4))
    except Exception as exc:
        raise ValueError("invalid_session_token_encoding") from exc


def _json_segment(segment: str) -> dict[str, Any]:
    try:
        value = json.loads(_decode_segment(segment))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid_session_token_payload") from exc
    if not isinstance(value, dict):
        raise ValueError("invalid_session_token_payload")
    return value


class HS256SessionVerifier:
    """Validate host-issued HS256 JWTs and return trusted identity claims."""

    def __init__(
        self,
        secret: str | bytes,
        *,
        issuer: str,
        audience: str,
        clock: callable = time.time,
        leeway_seconds: int = 30,
    ):
        key = secret.encode() if isinstance(secret, str) else secret
        if not isinstance(key, bytes) or len(key) < 32:
            raise ValueError("session_signing_secret_must_be_at_least_32_bytes")
        if not issuer or not audience:
            raise ValueError("session_issuer_and_audience_required")
        if not isinstance(leeway_seconds, int) or not 0 <= leeway_seconds <= 120:
            raise ValueError("invalid_session_clock_leeway")
        self._key = key
        self._issuer = issuer
        self._audience = audience
        self._clock = clock
        self._leeway = leeway_seconds

    def __call__(self, token: Any) -> dict[str, Any]:
        if not isinstance(token, str) or len(token) > 8192:
            raise PermissionError("invalid_session_token")
        parts = token.split(".")
        if len(parts) != 3:
            raise PermissionError("invalid_session_token")
        header = _json_segment(parts[0])
        claims = _json_segment(parts[1])
        if header.get("alg") != "HS256" or header.get("typ") not in (None, "JWT"):
            raise PermissionError("unsupported_session_token_algorithm")
        signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
        supplied = _decode_segment(parts[2])
        expected = hmac.new(self._key, signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(supplied, expected):
            raise PermissionError("invalid_session_token_signature")

        now = self._clock()
        exp = claims.get("exp")
        nbf = claims.get("nbf", 0)
        if isinstance(exp, bool) or not isinstance(exp, (int, float)):
            raise PermissionError("session_expiry_required")
        if isinstance(nbf, bool) or not isinstance(nbf, (int, float)):
            raise PermissionError("invalid_session_not_before")
        if now >= exp + self._leeway:
            raise PermissionError("session_token_expired")
        if now + self._leeway < nbf:
            raise PermissionError("session_token_not_yet_valid")
        if claims.get("iss") != self._issuer:
            raise PermissionError("session_issuer_mismatch")
        aud = claims.get("aud")
        if aud != self._audience and not (
            isinstance(aud, list) and self._audience in aud
        ):
            raise PermissionError("session_audience_mismatch")

        subject = claims.get("sub")
        workspace = claims.get("workspace_id")
        if not isinstance(subject, str) or not subject.strip() or len(subject) > 256:
            raise PermissionError("trusted_subject_missing")
        if not isinstance(workspace, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", workspace
        ):
            raise PermissionError("trusted_workspace_invalid")
        return {
            "authenticated": True,
            "subject": subject.strip(),
            "workspace_id": workspace,
        }
