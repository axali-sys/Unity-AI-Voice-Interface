# Trusted Execution Control Plane

## Purpose

`xparallel/trusted_execution.py` composes the trusted host repositories and
verified entity action gate with the immutable execution approval registry.
It is the next control-plane layer between authenticated digital entities and
a separately controlled worker.

## Enforced before an intent is recorded

- The external session is authenticated by the host adapter.
- The request's workspace comes from the authenticated principal.
- The entity, key, and capability are resolved from authoritative local
  registries by the trusted host adapter.
- The artifact digest is resolved independently of the entity manifest and
  must match the digest pinned into the proposed intent.
- The verified action gate must allow the exact action and resource scope.
- The intent registry records the canonical immutable request and digest.

## Approval and worker lifecycle

The existing approval registry continues to enforce a different approver from
the requester, a one-use expiring ticket, an authorized executor, and current
state checks before start and at worker checkpoints. The control plane now
provides those current-state checks by re-resolving the trusted artifact and
re-running the verified action gate. A revoked grant, stale artifact, missing
entity/key, or gate dependency failure blocks the checkpoint.

## Boundary and limitations

This module creates and governs execution intents; it does not launch a worker,
connect an HTTP route, or produce a production execution receipt. Host-supplied
approval, cancellation, and executor policy adapters remain mandatory. Local
SQLite repositories are development persistence, not distributed durable
storage. The integration tests use explicit fake host adapters and prove
composition behavior only; they are not production identity or sandbox tests.

The existing JWT-mode `/execute` and `/experiment` routes remain disabled.
No live environment, production service, or deployment setting is changed.
