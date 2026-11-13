# M2.12 — Execution Approval, Job Lifecycle and Revocation

Status: **local implementation; CI verification pending; not connected to an executor**.

## Implemented

- Immutable, digest-addressed job intents bind workspace, entity, signing key, capability, action, exact resource scope, payload SHA-256, artifact SHA-256, runner-image SHA-256 and bounded execution limits.
- A separate authenticated approver must approve or deny; the requester cannot approve their own job.
- Approval issues a random one-time ticket. Only its SHA-256 hash is stored; the ticket is returned once and bound to the exact intent.
- Ticket expiry is bounded by both the intent expiry and approval-ticket TTL.
- Start checks executor authorization and calls the mandatory current-state/revocation adapter immediately before the job transitions to running. Ticket use is one-time.
- Running work has a checkpoint method that rechecks current authorization/revocation; a false result tells the executor to stop immediately.
- Cancellation invalidates unused tickets and moves requested, approved or running jobs to a terminal cancelled state.
- Completion records success, failure or blocked outcomes and prevents a second terminal transition.
- Events record request, approval/denial, start, cancellation and completion. SQLite is local development state, not immutable distributed audit.

## Mandatory integration blockers

- This registry does not execute jobs or kill a running process. The future executor must call `check_running` at safe checkpoints and stop on a false result.
- Host authentication, requester/approver/executor role policy, artifact provenance and current entity/key/capability/grant revocation state are mandatory injected adapters; no production identity provider is configured.
- Approval tickets are bearer secrets. A production host must deliver them securely, protect transport, and ensure the runner never logs them.
- The existing HTTP routes and Docker runner are not wired to this lifecycle. No route may launch work until approval, ticket consumption, revocation checks, and cancellation are enforced end-to-end.

## Acceptance status

The local lifecycle implementation and unit tests are added in this milestone. M2.12 remains incomplete until CI passes and the ticket is integrated with a separately reviewed executor that enforces cancellation and revocation during execution.
