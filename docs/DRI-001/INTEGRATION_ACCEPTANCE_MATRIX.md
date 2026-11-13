# DRI-001 — Integration acceptance and evidence matrix

Status: integration planning and local CI evidence register; no production acceptance.

| Boundary / subsystem | Required integration evidence | Current state | Acceptance status |
|---|---|---|---|
| Authentication → workspace context | Trusted server session, tenant derivation, cross-tenant denial | Injected host adapter only; current routes not migrated | Blocked |
| Digital DNA → identity trust | Manifest digest, active key, proof-of-possession, owner binding | Local registries and unit tests | Partial |
| Identity → governance → action gate | Exact subject/entity/key/action/resource/expiry grant | Local composition gate; no route enforcement | Partial |
| Capability verification → artifact store | Immutable artifact provenance and expiry/revocation | Injected artifact trust root; no real store | Blocked |
| Approval ticket → execution worker | One-time ticket, executor binding, checkpoints, cancellation | Ticket lifecycle prototype; no connected executor | Partial |
| Worker → signed receipt | Authoritative terminal state, signer, resource/evidence provenance | Receipt primitive; no live worker | Partial |
| Messaging → secure transport | Signed/encrypted envelope, secure key exchange, TLS, ack | Local crypto/outbox; no network delivery | Partial |
| Federation → peer registry | Trust roots, transparency, replication, revocation | Local registry only | Partial |
| Memory → key management | KMS custody/rotation, scoped ACL, deletion verification | Local injected key resolver | Partial |
| Cognitive runtime → tools | Model output untrusted, verified gate, human approval, receipts | Proposal-only runtime; no tool execution | Partial |
| Parallel Intelligence → Omni | Durable tasks, verified contributions, approvals and receipts | Separate local primitives | Partial |
| Omni → execution lifecycle | Durable scheduler, worker leases, ticket and receipt integration | Adapter-driven orchestrator; not wired | Partial |
| Parallel Verse → scheduler | Authenticated workspace/space ACL, durable tasks and workers | SQLite service prototype | Partial |
| Evolution → deployment | Signed datasets, independent eval, canary, approval, rollback | Record-only proposal lifecycle | Blocked |
| Reality interface → physical world | Device identity, operator consent, safety interlocks, emergency stop | Simulation-only; no external connector | Blocked |
| Storage → recovery | Encrypted backup, restore rehearsal, external anchor | Local SQLite backup primitives | Partial |
| CI → release artifact | Pinned dependencies/actions, SBOM, vulnerability scan, signed provenance | CI test workflows only | Blocked |

## Cross-module acceptance sequence
1. A real authenticated session resolves one immutable workspace and subject.
2. Entity registration is validated; a key proves possession and is active/revocable.
3. An owner request and separate governance approval produce a narrowly scoped grant.
4. A trusted artifact is independently tested; evidence is tied to exact version and digest.
5. A proposed action passes the verified action gate and receives a one-time human approval ticket.
6. A worker checks revocation before and during work, stops on denial/cancellation, and emits an authoritative terminal record.
7. A receipt is signed and chained; an independent verifier can validate the complete evidence chain.
8. Memory, messaging and federation enforce the same tenant and key boundaries.
9. All negative cases fail closed: invalid auth, wrong tenant, wrong key, stale evidence, missing grant, expired/replayed ticket, revoked entity, runner timeout, receipt failure and malformed payload.
10. Recovery, incident response, monitoring, privacy and independent security reviews are demonstrated.

Passing isolated unit tests does not satisfy these cross-module acceptance conditions.
