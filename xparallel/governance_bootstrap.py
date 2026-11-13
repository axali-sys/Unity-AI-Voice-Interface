"""Explicit, fail-closed bootstrap for XParallel entity governance.

Activation requires a verified host JWT verifier, an explicit opt-in, and
absolute database paths supplied by the host. The host must place those paths
on durable storage; this module cannot make ephemeral disks durable.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

from xparallel.digital_dna import DigitalDNARegistry
from xparallel.entity_governance import EntityGovernanceRegistry


_ALLOWED_OPERATIONS = {"audit", "approve", "suspend", "reinstate", "revoke"}


def build_entity_governance(
    verifier: Callable[[str], dict[str, Any]] | None,
    *,
    environ: dict[str, str] | None = None,
) -> EntityGovernanceRegistry | None:
    """Build registry only when host explicitly supplies trusted identity and durable DB paths."""
    env = os.environ if environ is None else environ
    if env.get("XP_GOVERNANCE_ENABLE", "").strip().lower() not in {"1", "true", "yes"}:
        return None
    if not callable(verifier):
        return None

    dna_path = env.get("XP_DNA_DB_PATH", "").strip()
    governance_path = env.get("XP_GOVERNANCE_DB_PATH", "").strip()
    if not dna_path or not governance_path:
        return None
    if not Path(dna_path).is_absolute() or not Path(governance_path).is_absolute():
        raise ValueError("governance_database_paths_must_be_absolute")

    dna = DigitalDNARegistry(dna_path)

    def authenticate(token: Any) -> dict[str, Any]:
        claims = verifier(token)
        if not isinstance(claims, dict) or claims.get("authenticated") is not True:
            raise PermissionError("trusted_session_required")
        return claims

    def resolve_owner(workspace_id: str, entity_id: str) -> str | None:
        record = dna.get(workspace_id, entity_id)
        if not record:
            return None
        owner = record.get("manifest", {}).get("owner", {})
        subject = owner.get("subject") if isinstance(owner, dict) else None
        return subject if isinstance(subject, str) and subject.strip() else None

    def authorize_governance(principal: dict[str, Any], entity_id: str, operation: str) -> bool:
        if operation not in _ALLOWED_OPERATIONS:
            return False
        owner = resolve_owner(principal["workspace_id"], entity_id)
        return principal["subject"] == owner or principal.get("role") == "admin"

    return EntityGovernanceRegistry(
        authenticate=authenticate,
        resolve_owner=resolve_owner,
        authorize_governance=authorize_governance,
        db_path=governance_path,
    )
