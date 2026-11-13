# XParallel Secure Entity Communication Gateway — Draft 0.1

## Purpose

Provide a local, pull-based routing gateway between registered XParallel entities. The gateway verifies signed envelopes, requires trusted session authentication and explicit send/receive authorization, stores a queue entry, and exposes an authenticated recipient pull operation.

## Trust boundary

Two adapters are mandatory and injected by the host:
- `authenticate(session)` returns trusted server-side identity context: authenticated, workspace ID, entity ID, and subject.
- `authorize(identity, metadata, direction)` evaluates the application's explicit grants and returns `allowed: true` only when the exact send or receive permission is approved.

The gateway does not accept identity claims from the message body, infer identity from a bearer token, or treat a valid signature as authorization. A valid signature proves control of a registered key only.

## Flow

1. Sender presents a session and signed message envelope.
2. Gateway obtains trusted sender identity and checks workspace and sender entity match.
3. Send authorization is evaluated before message acceptance.
4. The message service verifies schema, digest, timestamps, active sender key, signature, and replay status.
5. Gateway stores the envelope in a workspace-scoped SQLite queue and records a queued event.
6. Recipient authenticates independently and pulls its pending inbox.
7. Receive authorization is evaluated for each message. Unauthorized messages remain queued.
8. Authorized messages are marked delivered once and returned with message provenance fields.
9. Sender/recipient may inspect message status; unrelated entities are denied. Audit events are workspace-scoped.

## Operational semantics

- Pull-based delivery only; no websocket, push notification, external network transport, retries, or exactly-once end-to-end guarantee.
- The local SQLite queue and audit table are single-instance development storage. They are not a distributed queue, tamper-proof audit ledger, or guaranteed durable production store.
- The gateway stores signed but unencrypted message bodies. Do not place secrets or sensitive personal data in messages.
- Delivery is marked before the response is returned. A process/network failure after marking may mean the caller does not receive the response; this prototype does not implement acknowledgement/retry semantics.
- The authentication adapter must bind authenticated subjects to active entities and trusted workspaces.
- The authorization adapter must apply the explicit grant model and enforce least privilege for both send and receive.
- Expired messages are marked expired at pull time and are not returned. A production gateway still needs scheduled retention/cleanup.
- Audit visibility is restricted to the sender and recipient entity. A database-backed audit table is queryable but not immutable against privileged database modification.

## Production requirements

Before route integration: implement and independently test trusted session authentication, owner-to-entity binding, grant persistence/revocation, active entity lifecycle checks, transport security, durable shared queue and replay protection, expiry cleanup, rate/size limits, transactional acknowledgement/retry semantics, key revocation propagation, monitoring, retention policy, backup/restore, and independent security review.

## Status

Draft local gateway prototype only. No HTTP routes are added and no existing public/private endpoint is changed by this milestone.
