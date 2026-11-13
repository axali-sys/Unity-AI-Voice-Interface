"""Concrete repository adapters for the XParallel verified action boundary.

Authentication and artifact provenance remain host-supplied trust roots. This
module composes those roots with the local Digital DNA, key, grant, and
capability-evidence repositories; it never reads identity or workspace claims
from an action request body.
"""
from __future__ import annotations

import re
from typing import Any, Callable

from xparallel.capability_verification import CapabilityVerificationLab
from xparallel.digital_dna import DigitalDNARegistry
from xparallel.entity_governance import EntityGovernanceRegistry
from xparallel.identity_trust import EntityKeyStore
from xparallel.verified_action_gate import VerifiedEntityActionGate

_SHA256 = re.compile(r"^[a-f0-9]{64}$")


def _trusted_principal(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or value.get("authenticated") is not True:
        raise PermissionError("caller_not_authenticated")
    subject = value.get("subject")
    workspace = value.get("workspace_id")
    if not isinstance(subject, str) or not subject.strip() or len(subject) > 200:
        raise PermissionError("trusted_subject_missing")
    if not isinstance(workspace, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,199}", workspace):
        raise PermissionError("trusted_workspace_missing")
    return {"authenticated": True, "subject": subject, "workspace_id": workspace}


class TrustedHostAdapters:
    """Build a fail-closed action gate from authoritative local repositories.

    authenticate(session) must validate a server-side session/token and return
    {authenticated: True, subject, workspace_id}. It must not decode unsigned
    client claims or accept a workspace supplied in an action body.

    resolve_artifact(workspace_id, entity_id, capability_id, version) must
    return trusted artifact metadata {version, artifact_digest}. The digest
    must describe the exact artifact that the sandbox would execute.

    The local SQLite repositories are development adapters, not distributed or
    tamper-proof stores. No HTTP route is activated by constructing this class.
    """

    def __init__(
        self,
        *,
        authenticate: Callable[[Any], dict[str, Any]],
        dna_registry: DigitalDNARegistry,
        key_store: EntityKeyStore,
        governance: EntityGovernanceRegistry,
        verification_lab: CapabilityVerificationLab,
        resolve_artifact: Callable[[str, str, str, str], dict[str, Any] | None],
    ):
        dependencies = (
            authenticate, dna_registry, key_store, governance,
            verification_lab, resolve_artifact,
        )
        if not all(callable(x) for x in (authenticate, resolve_artifact)):
            raise TypeError("trusted_authentication_and_artifact_adapters_required")
        if not isinstance(dna_registry, DigitalDNARegistry):
            raise TypeError("digital_dna_registry_required")
        if not isinstance(key_store, EntityKeyStore):
            raise TypeError("entity_key_store_required")
        if not isinstance(governance, EntityGovernanceRegistry):
            raise TypeError("entity_governance_registry_required")
        if not isinstance(verification_lab, CapabilityVerificationLab):
            raise TypeError("capability_verification_lab_required")
        self._authenticate = authenticate
        self._dna = dna_registry
        self._keys = key_store
        self._governance = governance
        self._lab = verification_lab
        self._resolve_artifact = resolve_artifact

    def authenticate(self, session: Any) -> dict[str, Any]:
        raw = self._authenticate(session)
        if not isinstance(raw, dict) or raw.get("authenticated") is not True:
            return {"authenticated": False}
        return _trusted_principal(raw)

    def resolve_entity_context(
        self, principal: dict[str, str], entity_id: str, key_id: str, capability_id: str,
    ) -> dict[str, Any]:
        trusted = _trusted_principal(principal)
        record = self._dna.get(trusted["workspace_id"], entity_id)
        if not isinstance(record, dict):
            raise LookupError("entity_not_found_in_authenticated_workspace")
        manifest = record.get("manifest")
        if not isinstance(manifest, dict) or manifest.get("entity_id") != entity_id:
            raise ValueError("invalid_authoritative_entity_record")

        capability = next((
            item for item in manifest.get("capabilities", [])
            if isinstance(item, dict) and item.get("capability_id") == capability_id
        ), None)
        if capability is None:
            raise LookupError("capability_not_declared_by_entity")

        key = self._keys.get_key(trusted["workspace_id"], entity_id, key_id)
        if not isinstance(key, dict):
            raise LookupError("entity_signing_key_not_found")
        if (key.get("workspace_id") != trusted["workspace_id"]
                or key.get("entity_id") != entity_id or key.get("key_id") != key_id):
            raise ValueError("authoritative_key_scope_mismatch")

        # Never trust a manifest's self-declared capability status or digest.
        # Artifact metadata must come from a separate trusted host resolver.
        version = capability.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ValueError("capability_version_missing")
        artifact = self._resolve_artifact(
            trusted["workspace_id"], entity_id, capability_id, version
        )
        if not isinstance(artifact, dict) or artifact.get("version") != version:
            raise LookupError("trusted_artifact_metadata_unavailable")
        digest = artifact.get("artifact_digest")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            raise ValueError("trusted_artifact_digest_invalid")

        owner = manifest.get("owner")
        owner_subject = owner.get("subject") if isinstance(owner, dict) else None
        if not isinstance(owner_subject, str) or not owner_subject.strip():
            raise ValueError("authoritative_owner_missing")

        return {
            "owner_subject": owner_subject,
            "entity_status": manifest.get("status"),
            "key_status": key.get("status"),
            "capability_version": version,
            "artifact_digest": digest,
        }

    def load_active_grants(
        self, principal: dict[str, str], entity_id: str,
    ) -> list[dict[str, Any]]:
        trusted = _trusted_principal(principal)
        return self._governance.active_grants(trusted["workspace_id"], entity_id)

    def build_action_gate(self) -> VerifiedEntityActionGate:
        """Return the decision-only gate; callers must still enforce its result."""
        return VerifiedEntityActionGate(
            authenticate=self.authenticate,
            resolve_entity_context=self.resolve_entity_context,
            load_active_grants=self.load_active_grants,
            verification_lab=self._lab,
        )
