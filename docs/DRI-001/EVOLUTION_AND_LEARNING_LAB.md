# DRI-001 — Evolution and learning laboratory

Status: partial local foundation; no live self-modification.

## Implemented
- Authenticated workspace-scoped experiment registry.
- Baseline/candidate version comparison with canonical dataset/config SHA-256 digests.
- Evaluation results and regression records stored with provenance.
- Versioned artifact proposals bound to a SHA-256 digest.
- Separate human approval checks for staging and promotion.
- Append-only-by-interface lifecycle event history for propose/stage/promote/rollback.
- Rollback state transition records; no runtime rollback is performed.
- Tests cover digest capture, approval gates, regression blocking, workspace isolation and record-only rollback.

## Not operational
- Evaluation runner is an injected adapter; no model training or live model evaluation is bundled.
- No dataset repository, signed dataset provenance, benchmark quality governance or independent reproducibility service.
- Promotion is a record only; no deployment, weight mutation, code patch or capability change occurs.
- Rollback is a record only; no live runtime state is reverted.
- No canary orchestration, telemetry, drift monitor, staged traffic, artifact registry, cryptographic event log or security review.

This laboratory does not authorize autonomous self-modification. Every promotion requires separate human approval and future runtime integration must preserve verification, rollback and audit controls.
