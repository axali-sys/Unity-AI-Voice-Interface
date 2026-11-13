# DRI-001 — Secure network transport foundation

Status: partial implementation; not a deployed network transport.

## Implemented
- AES-256-GCM encryption for already-signed entity-message envelopes.
- Authenticated additional data binds protocol version, workspace, recipient entity and recipient key ID.
- Recipient keys are injected by a trusted host and never persisted here.
- Strict recipient/workspace/key matching, tamper detection and bounded packet size.
- SQLite outbox with idempotent enqueue, pending queue quota, per-sender rate window, bounded exponential retry, injected acknowledgement verification, dead-letter state and per-attempt revocation check.
- Tests cover encryption round-trip, tampering, wrong key/recipient, idempotency, acknowledgement, retry/dead-letter, revocation and queue quota.

## Not yet implemented / required before operational use
- Secure key agreement and rotation/distribution for recipient encryption keys.
- Real authenticated TLS network client/server, certificate validation and endpoint identity.
- Cryptographically authenticated acknowledgement implementation; only an injected verifier contract exists.
- Durable multi-node queue coordination, delivery leases, crash-safe concurrent workers and distributed rate limiting.
- Full schema negotiation, dead-letter review/replay administration, monitoring and cross-node tests.
- Integration with the entity gateway, HTTP routes and live authorization service.
- Revocation propagation between independent nodes and independent cryptographic/security review.

Confidentiality and integrity depend on the host supplying a secret 256-bit recipient key securely. This module does not provide key agreement, forward secrecy, peer identity or transport security by itself. The inner signed envelope must still be verified by the existing message service. Never log or expose encryption keys.

No production route is activated and no external network request or execution is performed.
