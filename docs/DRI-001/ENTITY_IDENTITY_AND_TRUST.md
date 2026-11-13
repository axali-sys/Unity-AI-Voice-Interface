# XParallel Entity Identity and Trust — Draft 0.1

## Purpose

Define a narrow trust layer for Digital DNA entities: proof that a party controls a registered signing key, safe key rotation, and governance-authorized key revocation.

This is a protocol and local prototype, not a complete identity provider or production trust service.

## Cryptographic profile

- Signature algorithm: Ed25519.
- Public keys: 32 raw bytes, Base64-encoded for transport.
- Signatures: Base64-encoded Ed25519 signatures.
- Private keys: generated and held by the entity owner in an external secure key provider; never uploaded to XParallel or written into a manifest/database.
- Fingerprints: SHA-256 of the raw public key.
- Messages: canonical UTF-8 JSON with sorted keys and compact separators, prefixed with a distinct protocol/domain label to prevent cross-protocol signature reuse.
- Implementation: maintained open-source `cryptography` package; no custom cryptographic primitives.

## Lifecycle

1. Submit a public key as `pending`.
2. Registry issues a random, one-use, short-lived challenge scoped to workspace, entity, and key ID.
3. The key holder signs the exact domain-separated challenge bytes.
4. Registry verifies the signature against the registered public key and activates the key.
5. Key rotation requires both the existing active key to authorize the new key fingerprint and the new key to prove possession of its private key. Successful rotation marks the old key `rotated` and the new key `active`.
6. Emergency revocation requires a signature from a separately configured governance authority key. The authority public key must be provisioned out-of-band; it is not self-issued by an entity.
7. Inactive keys cannot be used as active keys for future trust operations.

## Security boundaries

- A valid Ed25519 proof establishes control of a private key at the time of challenge. It does **not** prove a person's legal identity, organization ownership, or rightful control of an entity.
- Binding a key to the manifest's `owner.subject` requires a separately authenticated owner/workspace identity service. That binding is not implemented here.
- Key activation does not activate the entity manifest, certify capabilities, grant scopes, or authorize tool/runtime execution.
- The governance authority public key must be protected and rotated under a documented out-of-band process. A compromised authority key can revoke entity keys.
- SQLite storage is a development prototype, not a tamper-proof trust ledger or multi-node consistency service.
- No API routes or production key-management integration are included in this milestone.

## Required controls before production

- Authenticated workspace and entity authorization at every API boundary.
- Hardware-backed or OS-protected private-key storage where available.
- Governance authority key ceremony, backup, rotation, and recovery.
- Rate limits and abuse controls for challenge issuance.
- Atomic database transactions and concurrency tests across supported deployment topology.
- Audit export to an independently protected append-only log.
- Formal threat model, independent cryptographic review, dependency scanning, and security testing.
- Explicit user/administrator approval for ownership transfer and consequential actions.

## Test coverage

The accompanying tests cover successful and failed proof-of-possession, one-time challenges, workspace scoping, dual-control rotation, and authority-signed revocation. Test files are not evidence of passing tests until CI or a local test run reports success.
