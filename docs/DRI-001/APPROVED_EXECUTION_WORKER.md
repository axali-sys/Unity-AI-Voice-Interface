# Approval-Bound Execution Worker

## Implemented components

- `xparallel/execution_worker.py` consumes an approved one-time ticket and
  starts the execution lifecycle using the authenticated worker session.
- It loads the payload from a trusted adapter and recomputes the canonical
  SHA-256 digest before execution.
- It independently resolves the artifact digest and compares it with the
  approved immutable intent.
- It passes the approved limits and exact runner image digest to the sandbox.
- The sandbox runner now refuses missing/mismatched approved limits and image
  digests, ensures configured Docker ceilings do not exceed the approval, and
  truncates output to the approved byte limit.
- The runner invokes a live authorization checkpoint while draining process
  output. If the checkpoint denies continuation, it kills the worker process
  group and returns a blocked result.
- The worker obtains current policy evidence, measured resource usage, and
  persisted evidence references before finalization.
- The lifecycle now transitions from `running` to nonterminal `finalizing`.
  The signed receipt is appended against that authoritative finalizing record;
  only after append succeeds does the registry transition to `completed` or
  `failed`.
- If evidence preparation or receipt append fails, the job remains
  `finalizing` with `receipt_pending: true`; it is not falsely reported as
  terminal. This is a durable pending marker, not yet an automated recovery
  worker or transactional outbox. Operators still need a controlled recovery
  path to reconstruct/retry pending receipt creation.

## Mandatory trusted adapters

The worker intentionally cannot invent operational evidence. A deployment
must supply:
- trusted payload loader;
- authoritative artifact digest resolver;
- policy/grant and verification-evidence resolver;
- resource meter reporting actual wall, CPU, memory, output and PID use;
- evidence store returning durable evidence references;
- trusted receipt signer and verifier already required by the ledger.

If these adapters are missing, invalid, or unable to provide evidence, no
receipt is fabricated. The worker does not expose an HTTP route and is not
enabled in the live server.

## Security boundary

The Docker runner still uses a digest-pinned image, no network, read-only root,
non-root UID, dropped capabilities, no-new-privileges, seccomp, bounded
resources, a disposable workspace and bounded output. These are defense-in-depth
controls, not proof of hostile-code isolation. A Docker daemon compromise,
kernel escape, host configuration weakness, or insufficient filesystem policy
remains possible. Production use requires a hardened microVM/container host,
independent security review, durable signing-key management, and tested
resource metering.

## Test scope

Unit tests verify ticket consumption, payload tamper rejection, artifact
mismatch rejection, revocation denial, approved-limit forwarding, and that
measurement/storage failures prevent a success terminal status. Tests use
injected runners/adapters; no real Docker workload or live identity provider
is invoked.


## Pending receipt recovery

The approval registry now persists the exact receipt package (policy decision,
start time, measured resource usage and immutable evidence references) in the
same SQLite transaction that changes a job to `finalizing`. The package is
workspace-scoped and can be read for recovery only by the executor identity
bound to that job.

`ApprovedExecutionWorker.recover_finalization(session, intent_id)` first
checks the signed receipt ledger for an already committed receipt. If one is
present and the chain verifies, it completes the pending job without appending
a duplicate. If no receipt exists, it retries the append using the persisted
package and then completes the job. It never re-launches the workload or
re-measures resources.

This closes the receipt-append/terminal-state crash window for jobs whose
receipt package was persisted. Jobs that entered finalizing because policy,
measurement or evidence storage itself failed have no complete receipt package;
they remain pending and require separate operator remediation. The recovery
method is an application API, not yet exposed as an authenticated HTTP route or
scheduled recovery service. The SQLite database still requires a persistent
host volume and backup/recovery controls.
