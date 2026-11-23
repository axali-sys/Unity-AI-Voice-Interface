"""Memory Continuity Governance (MCG) policy primitives.

This module defines fail-closed lifecycle decisions for the existing memory vault.
It does not claim transactional snapshots or automatic recovery; those require a
storage adapter with versioning and integrity verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class Operation(str, Enum):
    CONSERVE = "conserve"
    TRANSFORM = "transform"
    ERASE = "erase"
    RESET_EXECUTION = "reset_execution"
    RECOVER = "recover"


class MemoryClass(str, Enum):
    IDENTITY = "identity"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    EPISODIC = "episodic"
    WORKING = "working"
    EXECUTION = "execution"


PROTECTED_CLASSES = frozenset({
    MemoryClass.IDENTITY,
    MemoryClass.SEMANTIC,
    MemoryClass.PROCEDURAL,
})


@dataclass(frozen=True)
class LifecycleRequest:
    operation: Operation
    memory_class: MemoryClass | None = None
    authorized: bool = False
    retention_expired: bool = False
    source_verified: bool = False
    result_verified: bool = False
    explicit_scope: bool = False


@dataclass(frozen=True)
class LifecycleDecision:
    allowed: bool
    action: str
    reason: str


def decide(request: LifecycleRequest) -> LifecycleDecision:
    """Pure policy decision; callers must enforce it before storage mutation."""
    op = request.operation

    if op is Operation.RESET_EXECUTION:
        return LifecycleDecision(True, "clear_ephemeral_execution_only",
                                 "execution reset cannot implicitly erase durable memory")

    if op is Operation.CONSERVE:
        return LifecycleDecision(True, "preserve_source_and_lineage",
                                 "conservation is non-destructive")

    if op is Operation.TRANSFORM:
        if not request.source_verified:
            return LifecycleDecision(False, "quarantine_or_reject",
                                     "transformation requires verified source")
        if not request.result_verified:
            return LifecycleDecision(False, "retain_source_reject_result",
                                     "unverified derived memory cannot replace source")
        return LifecycleDecision(True, "append_derived_version",
                                 "verified transformation preserves source lineage")

    if op is Operation.ERASE:
        if not request.authorized or not request.explicit_scope:
            return LifecycleDecision(False, "deny",
                                     "erasure requires authorization and explicit scope")
        if request.memory_class in PROTECTED_CLASSES and not request.retention_expired:
            return LifecycleDecision(False, "deny",
                                     "protected memory requires applicable deletion authority")
        return LifecycleDecision(True, "erase_scoped_record",
                                 "authorized scope and retention policy permit deletion")

    if op is Operation.RECOVER:
        if not request.source_verified:
            return LifecycleDecision(False, "quarantine",
                                     "recovery source integrity is not verified")
        return LifecycleDecision(True, "restore_verified_version",
                                 "recovery source passed integrity verification")

    return LifecycleDecision(False, "deny", "unknown lifecycle operation")


def audit_metadata(request: LifecycleRequest, decision: LifecycleDecision) -> dict[str, Any]:
    """Minimal non-content audit record; never include memory payloads or credentials."""
    return {
        "operation": request.operation.value,
        "memory_class": request.memory_class.value if request.memory_class else None,
        "allowed": decision.allowed,
        "action": decision.action,
        "reason": decision.reason,
    }
