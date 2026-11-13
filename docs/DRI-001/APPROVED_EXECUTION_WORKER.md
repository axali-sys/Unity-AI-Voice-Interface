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
- If evidence preparation is incomplete, the worker now creates a signed
  non-success receipt where unavailable measurements are explicitly `null`,
  policy evidence failure is explicitly denied with a reason code, and missing
  evidence references remain an empty list. It never substitutes zero or a
  fabricated allowed decision. Success receipts still require complete measured
  values, an allowed policy decision and evidence references.
- If receipt append itself fails, the job remains `finalizing` with
  `receipt_pending: true`; the immutable receipt package supports retry without
  rerunning the workload.

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
bound to that job. It is stored with a SHA-256 integrity digest and protected by a SQLite trigger against modification after finalization; recovery rechecks the digest before use.

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
scheduled recovery service. A raw registry must be configured with a trusted
receipt verifier before it can complete any finalization; the default is deny. The SQLite database still requires a persistent
host volume and backup/recovery controls.


## Bounded pending-receipt recovery batches

The registry exposes a bounded listing of pending finalizations scoped to the
authenticated executor and workspace. The worker can process this list in
batches of 1–100 jobs. Each item is recovered independently, so one failed
receipt does not prevent later jobs from being attempted. This batch API is
suitable for a future authenticated host scheduler, but no scheduler, HTTP
endpoint, background process, or automatic startup recovery is enabled.


## Explicitly incomplete failure evidence

The receipt schema now distinguishes verified values from unavailable values
for non-success outcomes. For a failed or blocked execution, a resource field
may be `null` only when the host could not measure it; a policy failure is
recorded as `allowed: false` with a stable reason code; and evidence references
may be empty. These exceptions are prohibited for successful receipts. This
allows a signed, auditable failure record without inventing telemetry or
claiming that policy allowed the action.

The tests cover a signed failure receipt with unavailable metrics, denied
policy evidence and no stored evidence references, plus rejection of the same
incomplete package for a success receipt.

## Supervised host-side receipt recovery

`xparallel/execution_recovery_service.py` adds an explicitly host-invoked
single-flight recovery loop. Each cycle obtains a fresh short-lived executor
session from a host-supplied session provider and calls the worker's bounded
recovery API (default batch size 25, maximum 100). The registry independently
authenticates the session and limits the query to pending jobs owned by that
executor in its workspace.

The service:
- never launches, resumes, or repeats a workload;
- recovers only receipts from persisted immutable finalization packages;
- skips overlapping cycles rather than running duplicate recovery work;
- rejects missing sessions and malformed recovery summaries;
- retries after transient failures using a fresh session on the next cycle;
- supports explicit shutdown through a host supervisor stop event.

The service is not started by module import or by the HTTP server. A host
operator must deliberately construct it with a trusted executor-session
provider and run it under a supervised background process. This branch does
not configure a production identity provider, scheduler, persistent volume,
service manager, or live recovery process. The recovery loop and concurrency
behavior are unit-tested only; deployment and restart behavior remain
unverified.

## Explicit host supervisor lifecycle

`xparallel/execution_recovery_supervisor.py` provides the host lifecycle
wrapper. Construction is inert: it does not start a thread or perform recovery.
The host must pass the already-configured execution host services and trusted
short-lived executor-session provider, explicitly set `enabled=True`, and call
`start()`. The supervisor exposes a small health snapshot and a bounded
`stop()` operation that joins the worker thread.

The supervisor is deliberately not imported or started by `xparallel.server`.
There is no environment-variable shortcut that silently activates recovery.
This keeps the recovery process under the host's explicit lifecycle and
identity-management control. Unit tests cover disabled-by-default behavior,
explicit start, stop/join and timeout validation. No live host service manager,
identity provider, persistent volume or restart policy is configured by this
development branch.

### Recovery health and failure reporting

The supervisor health snapshot now reports enabled/running state, last cycle and successful-cycle timestamps, last sanitized exception class, consecutive/total failures, total recovered receipts and the most recent bounded batch counts. The optional host alert callback receives only the exception class name; exception messages, tokens and adapter details are deliberately excluded. A failed cycle is counted and the loop remains available for a later retry. These are in-process counters, not durable monitoring: they reset when the host process restarts and must be exported by a separately configured host monitoring adapter if durable alerting is required. No HTTP health route or external alert destination is configured by this branch.

### Persistent recovery health history

`xparallel/execution_recovery_health_store.py` adds an optional SQLite adapter for recovery health history. A host must explicitly construct `SQLiteExecutionRecoveryHealthStore` with a selected database path and inject it into `ExecutionRecoverySupervisor`; no database is created by import or default configuration. The store uses WAL, `synchronous=FULL`, and append-only update/delete guards. It records only cycle timestamps, bounded result counts, and exception class names—never session tokens, exception messages, payloads, or adapter details. The supervisor restores aggregate counters and the last result on construction, then appends subsequent success/failure events. If health persistence fails, recovery continues and the in-memory health snapshot exposes `health_store_error_type`; monitoring storage failure does not block receipt recovery. Tests cover close/reopen restoration, failure counter reset behavior, append-only enforcement, and supervisor restart restoration. Durability still depends on the host's actual persistent volume, backup policy, and SQLite operational controls; this is not external monitoring, tamper-proof remote audit, or a configured production host.

