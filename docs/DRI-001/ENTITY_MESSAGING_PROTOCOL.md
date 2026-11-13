# XParallel Entity Messaging Protocol — Draft 0.1

## Purpose

Define a signed message envelope that an XParallel entity can use to address another entity. This milestone provides a local verification and replay-detection prototype. It does not provide a network, queue, delivery guarantee, online discovery, or production transport.

## Envelope

Version 1.0 includes:
- unique message ID;
- workspace, sender entity, sender key, and recipient entity IDs;
- message type;
- UTC issue and expiry timestamps;
- JSON body and SHA-256 body digest;
- Ed25519 signature over canonical JSON, with the domain prefix `XPARALLEL-ENTITY-MESSAGE-V1`.

Canonical JSON sorts keys, removes insignificant whitespace, uses UTF-8, and rejects non-JSON values and NaN. The signature covers every envelope field except the signature itself.

## Sender requirements

1. The caller supplies a private Ed25519 key; the service never accepts or stores private key bytes.
2. The sender key must already exist in the trusted key store and have status `active`.
3. Message lifetime is limited to 1–86,400 seconds.
4. Message body is limited to 256,000 encoded bytes.

## Receiver requirements

1. The receiver supplies the expected workspace and recipient entity IDs from trusted local context, not from an untrusted message.
2. The message must have the exact required schema and identifiers.
3. Workspace and recipient must match the receiving context.
4. Body digest, timestamps, expiry, active sender-key status, and Ed25519 signature are checked.
5. The receiver inserts `(workspace_id, message_id)` into a SQLite table with a uniqueness constraint. A repeated ID is rejected.
6. Accepted messages return their body and provenance fields to the caller.

## Security boundaries and limitations

- Key possession proves control of a key, not legal identity, ownership legitimacy, capability certification, or permission to perform actions.
- The caller must authenticate the receiving session and obtain expected workspace/recipient values from trusted context.
- The local SQLite replay store is single-instance development state. It is not a distributed replay cache, immutable audit ledger, or guaranteed durable store.
- The message is signed but not encrypted. Do not put secrets or sensitive personal data in the body.
- The prototype does not transmit, queue, route, retry, acknowledge, or guarantee delivery.
- Clock skew is bounded; production deployments need reliable time synchronization.
- Production integration requires a trusted authentication adapter, durable shared replay protection, key revocation propagation, rate/size limits, transport security, monitoring, threat modelling, and independent security review.

## Conformance tests

The test suite checks valid signatures, body and header tampering, recipient and workspace mismatch, expiry, replay rejection, inactive sender keys, malformed envelopes, and absence of private-key storage.

## Status

Draft protocol and local prototype only. No API routes, production transport, or live entity-to-entity network are connected by this change.
