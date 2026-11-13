"""Fail-closed host service boundary for approved XParallel execution.

These adapters are integration contracts, not pretend implementations of
resource metering or durable storage. A deployment must inject trusted host
services that can substantiate their results.
"""
from __future__ import annotations

import re
from typing import Any, Callable

from xparallel.execution_worker import ApprovedExecutionWorker

_SHA256 = re.compile(r"^[a-f0-9]{64}$")
_USAGE_FIELDS = ("wall_ms", "cpu_ms", "memory_peak_mb", "output_bytes", "pids_peak")


def _required_sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ValueError(f"trusted_{field}_must_be_sha256")
    return value


class ExecutionHostServices:
    """Validate trusted host adapters and construct the approved worker.

    Required host adapters:
      - load_payload: retrieve immutable approved payload from authoritative storage
      - resolve_artifact_digest: resolve the exact executable artifact
      - resolve_policy_evidence: re-evaluate current grants and verification evidence
      - measure_resources: return measurements from the actual host/container runtime
      - store_evidence: persist execution evidence durably and return immutable references
      - receipts: signed receipt ledger with authoritative job lookup and signing

    The adapter implementations are trust roots. This wrapper validates their
    outputs but cannot independently prove that an operator's storage or
    measurement service is honest or durable.
    """

    def __init__(
        self, *, approvals: Any, runner: Callable[..., dict[str, Any]],
        load_payload: Callable[[dict[str, Any]], dict[str, Any]],
        resolve_artifact_digest: Callable[[dict[str, Any]], str],
        resolve_policy_evidence: Callable[[dict[str, Any]], dict[str, Any]],
        measure_resources: Callable[[dict[str, Any], dict[str, Any]], dict[str, int]],
        store_evidence: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
        receipts: Any,
    ):
        callbacks = (runner, load_payload, resolve_artifact_digest,
                     resolve_policy_evidence, measure_resources, store_evidence)
        if not all(callable(item) for item in callbacks):
            raise TypeError("all_trusted_execution_host_adapters_required")
        for method in ("start", "check_running", "finish"):
            if not callable(getattr(approvals, method, None)):
                raise TypeError("execution_approval_registry_incomplete")
        if not callable(getattr(receipts, "append", None)):
            raise TypeError("signed_execution_receipt_ledger_required")
        self.approvals = approvals
        self.runner = runner
        self._load_payload = load_payload
        self._resolve_artifact = resolve_artifact_digest
        self._resolve_policy = resolve_policy_evidence
        self._measure = measure_resources
        self._store = store_evidence
        self.receipts = receipts

    def load_payload(self, intent: dict[str, Any]) -> dict[str, Any]:
        payload = self._load_payload(intent)
        if not isinstance(payload, dict):
            raise ValueError("authoritative_execution_payload_unavailable")
        return payload

    def resolve_artifact_digest(self, intent: dict[str, Any]) -> str:
        digest = _required_sha(self._resolve_artifact(intent), "artifact_digest")
        if digest != intent.get("artifact_digest"):
            raise PermissionError("authoritative_artifact_digest_mismatch")
        return digest

    def resolve_policy_evidence(self, intent: dict[str, Any]) -> dict[str, Any]:
        evidence = self._resolve_policy(intent)
        if not isinstance(evidence, dict) or evidence.get("allowed") is not True:
            raise PermissionError("current_policy_evidence_denied_or_unavailable")
        for field in ("grant_id", "evidence_run_id"):
            value = evidence.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"trusted_policy_{field}_required")
        return evidence

    def measure_resources(self, result: dict[str, Any], intent: dict[str, Any]) -> dict[str, int]:
        usage = self._measure(result, intent)
        if not isinstance(usage, dict) or set(usage) != set(_USAGE_FIELDS):
            raise ValueError("complete_host_resource_measurement_required")
        for field in _USAGE_FIELDS:
            value = usage[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"invalid_host_resource_measurement:{field}")
        limits = intent.get("limits")
        if not isinstance(limits, dict):
            raise ValueError("approved_execution_limits_missing")
        wall_limit_ms = limits.get("timeout_seconds", 0) * 1000
        cpu_limit_ms = (usage["wall_ms"] * limits.get("cpu_millis", 0)) // 1000
        if (usage["wall_ms"] > wall_limit_ms
                or usage["cpu_ms"] > cpu_limit_ms
                or usage["memory_peak_mb"] > limits.get("memory_mb", 0)
                or usage["output_bytes"] > limits.get("output_bytes", 0)
                or usage["pids_peak"] > limits.get("pids", 0)):
            raise ValueError("host_resource_measurement_exceeds_approved_limits")
        return usage

    def store_evidence(self, result: dict[str, Any], intent: dict[str, Any]) -> list[str]:
        stored = self._store(result, intent)
        if not isinstance(stored, dict) or stored.get("durable") is not True:
            raise ValueError("durable_execution_evidence_storage_not_confirmed")
        refs = stored.get("references")
        if (not isinstance(refs, list) or not refs
                or any(not isinstance(ref, str) or not ref.strip() for ref in refs)
                or len(set(refs)) != len(refs)):
            raise ValueError("immutable_execution_evidence_references_required")
        return [ref.strip() for ref in refs]

    def build_worker(self) -> ApprovedExecutionWorker:
        return ApprovedExecutionWorker(
            approvals=self.approvals,
            runner=self.runner,
            load_payload=self.load_payload,
            resolve_artifact_digest=self.resolve_artifact_digest,
            resolve_policy_evidence=self.resolve_policy_evidence,
            measure_resources=self.measure_resources,
            store_evidence=self.store_evidence,
            receipts=self.receipts,
        )
