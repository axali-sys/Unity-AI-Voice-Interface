# M2.13 — Signed Execution Evidence and Provenance

Status: **local implementation; CI verification pending; no external anchor**.

## Implemented

- Receipts are generated only from an authoritative terminal job record supplied by a trusted host adapter; callers cannot submit replacement entity, artifact, runner or approval metadata.
- Each receipt binds the exact intent digest, payload/artifact/runner-image digests, entity/key/capability/action/resource scope, human approver and approval time, policy grant and verification run, execution timestamps, exit code/outcome, bounded resource usage and evidence references.
- Receipt digests form a per-workspace SHA-256 hash chain. A detached signature is created through an injected signer; private signing keys are never stored in the ledger.
- Chain verification recomputes every hash, checks previous-hash continuity and verifies every signature through an injected verifier.
- SQLite triggers reject ordinary UPDATE/DELETE attempts on receipt rows.

## Limitations

- The SQLite file and its triggers are not immutable against a privileged database/file administrator. The hash chain makes tampering detectable only while the trusted signing key and expected chain head remain protected.
- No external timestamping, transparency log, object-lock storage, or independent anchor is configured.
- Signing key custody, rotation, revocation and public-key distribution remain host responsibilities.
- Evidence references are identifiers only; this ledger does not upload, retain, encrypt or independently validate referenced artifacts.
- The executor and M2.12 lifecycle are not wired to a live runtime; no actual job receipt has been produced from a real sandbox run.

## Acceptance status

The local receipt ledger and unit tests are added. M2.13 remains incomplete until CI passes, the ledger is connected to the authoritative job lifecycle, evidence artifacts are stored under retention/access controls, and a separately controlled external anchor is designed and validated.
