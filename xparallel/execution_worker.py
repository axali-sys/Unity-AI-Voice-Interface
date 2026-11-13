"""Approval-bound execution worker; all host evidence and measurement adapters are injected.

The worker launches no code until the one-time ticket is consumed, the trusted
payload/artifact are checked, and a live revocation checkpoint passes.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Callable


def _canonical_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class ApprovedExecutionWorker:
    def __init__(
        self, *, approvals: Any, runner: Callable[..., dict[str, Any]],
        load_payload: Callable[[dict[str, Any]], dict[str, Any]],
        resolve_artifact_digest: Callable[[dict[str, Any]], str],
        resolve_policy_evidence: Callable[[dict[str, Any]], dict[str, Any]],
        measure_resources: Callable[[dict[str, Any], dict[str, Any]], dict[str, int]],
        store_evidence: Callable[[dict[str, Any], dict[str, Any]], list[str]],
        receipts: Any,
    ):
        adapters = (runner, load_payload, resolve_artifact_digest,
                    resolve_policy_evidence, measure_resources, store_evidence)
        if not all(callable(x) for x in adapters):
            raise TypeError("trusted_worker_adapters_required")
        if not callable(getattr(approvals, "start", None)) or not callable(getattr(approvals, "check_running", None)) or not callable(getattr(approvals, "begin_finalization", None)) or not callable(getattr(approvals, "complete_finalization", None)):
            raise TypeError("execution_approval_registry_required")
        if not callable(getattr(receipts, "append", None)):
            raise TypeError("execution_receipt_ledger_required")
        self._approvals = approvals
        self._runner = runner
        self._load_payload = load_payload
        self._resolve_artifact = resolve_artifact_digest
        self._resolve_policy = resolve_policy_evidence
        self._measure = measure_resources
        self._store_evidence = store_evidence
        self._receipts = receipts

    def execute(self, session: Any, one_time_ticket: str) -> dict[str, Any]:
        running = self._approvals.start(session, one_time_ticket)
        intent_id = running["intent_id"]
        intent = running["intent"]
        started_at = running["started_at"]

        def checkpoint() -> bool:
            try:
                result = self._approvals.check_running(session, intent_id)
                return isinstance(result, dict) and result.get("continue") is True
            except Exception:
                return False

        try:
            if not checkpoint():
                raise PermissionError("execution_revoked_before_worker_start")
            payload = self._load_payload(intent)
            if not isinstance(payload, dict) or _canonical_digest(payload) != intent["payload_digest"]:
                raise PermissionError("approved_payload_digest_mismatch")
            if self._resolve_artifact(intent) != intent["artifact_digest"]:
                raise PermissionError("approved_artifact_digest_mismatch")
            if not checkpoint():
                raise PermissionError("execution_revoked_before_runner_start")
            result = self._runner(
                payload,
                approved_limits=intent["limits"],
                expected_image_digest=intent["runner_image_digest"],
                should_continue=checkpoint,
            )
            if not isinstance(result, dict) or result.get("status") not in {"success", "failed", "blocked"}:
                result = {"status": "failed", "error": "runner_returned_invalid_result"}
            outcome = "success" if result["status"] == "success" else (
                "blocked" if result["status"] == "blocked" else "failure"
            )
        except PermissionError as exc:
            result = {"status": "blocked", "error": str(exc)}
            outcome = "blocked"
        except Exception as exc:
            result = {"status": "failed", "error": "worker_adapter_failure", "detail": type(exc).__name__}
            outcome = "failure"

        # Freeze the outcome first, but do not make it terminal until a signed
        # receipt has been appended. Failed evidence preparation remains recoverable.
        try:
            policy = self._resolve_policy(intent)
            if not isinstance(policy, dict) or policy.get("allowed") is not True:
                raise PermissionError("trusted_policy_evidence_unavailable_for_receipt")
            usage = self._measure(result, intent)
            evidence_refs = self._store_evidence(result, intent)
            if not isinstance(evidence_refs, list) or not evidence_refs:
                raise ValueError("execution_evidence_storage_required")
        except Exception as exc:
            finalizing = self._approvals.begin_finalization(
                session, intent_id, outcome="failure"
            )
            return {
                "intent_id": intent_id, "status": finalizing["status"],
                "outcome": "failure", "runner_result": result, "receipt": None,
                "receipt_pending": True, "error": "execution_evidence_pipeline_failed",
                "evidence_error": type(exc).__name__,
            }

        try:
            finalizing = self._approvals.begin_finalization(
                session, intent_id, outcome=outcome
            )
        except PermissionError:
            # A revocation racing with successful completion must downgrade
            # the recorded outcome, never leave a false success or running job.
            if outcome != "success":
                raise
            outcome = "blocked"
            result = {"status": "blocked", "error": "execution_revoked_or_stale_at_completion"}
            finalizing = self._approvals.begin_finalization(
                session, intent_id, outcome=outcome
            )
        try:
            receipt = self._receipts.append(
                session,
                intent_id=intent_id,
                policy_decision=policy,
                started_at=started_at,
                finished_at=finalizing["finished_at"],
                exit_code=0 if outcome == "success" else 1,
                resource_usage=usage,
                evidence_refs=evidence_refs,
            )
        except Exception as exc:
            return {
                "intent_id": intent_id, "status": "finalizing", "outcome": outcome,
                "runner_result": result, "receipt": None, "receipt_pending": True,
                "error": "execution_receipt_commit_failed",
                "receipt_error": type(exc).__name__,
            }

        terminal = self._approvals.complete_finalization(session, intent_id)
        return {
            "intent_id": intent_id, "status": terminal["status"],
            "outcome": outcome, "runner_result": result, "receipt": receipt,
            "receipt_pending": False,
        }

