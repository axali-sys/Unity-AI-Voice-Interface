"""Voice authentication integration contract.

This module deliberately does not identify a person from raw audio or store voice
biometrics. A configured identity provider must perform any sensitive verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class VoiceAuthResult:
    account_id: str | None
    verified: bool
    reason: str
    provider: str | None = None
    verified_at: str | None = None


def verification_result(
    *,
    account_id: str | None,
    verified: bool,
    reason: str,
    provider: str | None = None,
) -> VoiceAuthResult:
    return VoiceAuthResult(
        account_id=account_id if verified else None,
        verified=bool(verified),
        reason=str(reason),
        provider=provider,
        verified_at=datetime.now(timezone.utc).isoformat() if verified else None,
    )


def fail_closed(reason: str = "voice_identity_provider_required") -> VoiceAuthResult:
    return verification_result(
        account_id=None,
        verified=False,
        reason=reason,
    )
