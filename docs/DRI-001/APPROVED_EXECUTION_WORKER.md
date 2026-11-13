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
- Before committing a successful terminal status, the worker now obtains
  current policy evidence, measured resource usage, and persisted evidence
  references. If any evidence adapter fails, the worker closes the job as a
  failure and does not report success or append a receipt.
- After evidence preparation succeeds, the worker commits the terminal status
  and appends the signed receipt. A remaining crash window exists between
  terminal-state commit and receipt append; a transactional outbox/finalizing
  state is still required to eliminate it.

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
