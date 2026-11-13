# DRI-001 — Security threat model and validation plan

Status: engineering threat-model draft; **not an independent security assessment**.

## System boundary
The isolated branch contains local SQLite prototypes and injected host adapters for entity identity, capability evidence, authorization, messaging, execution approval/receipts, memory, model routing, collaboration, orchestration, federation, evolution and simulation-only connectors. Existing HTTP routes still use a shared bearer-token/client-workspace pattern in places. No production trust provider, distributed registry, live external transport, or hostile-code sandbox validation is established.

## Assets
1. Entity signing keys and key lifecycle state.
2. Owner/workspace identity and authentication sessions.
3. Capability claims, verification evidence and artifact digests.
4. Permission grants, approval tickets, revocation state and execution receipts.
5. Private messages, memory content, provenance and encryption keys.
6. Model prompts, tool proposals, workflow inputs and external connector scopes.
7. Local registries, SQLite files, backups, audit events and CI/release credentials.

## Trust boundaries
- User/device to HTTP service.
- HTTP service to trusted host authentication and workspace resolver.
- Entity manifest to registry validation.
- Entity key to signed message and identity proof.
- Governance approval to action authorization.
- Capability verifier to runner and artifact store.
- Orchestrator to executor and receipt signer.
- Local node to remote federation peer.
- Model output to tool proposal/approval.
- Memory service to host key-management and authorization adapters.
- Reality connector to external device/service (currently not connected).

## Threat register

| ID | Threat / abuse case | Required control | Current evidence / gap |
|---|---|---|---|
| T01 | Spoofed entity or stolen signing key | Proof-of-possession, key rotation/revocation, owner binding | Local Ed25519 primitives tested; no production identity proof or custody |
| T02 | Workspace/tenant data leakage | Server-derived tenant context, scoped queries, negative tests | Several local stores scoped; current HTTP workspace input remains a blocker |
| T03 | Forged capability or stale evidence | Artifact-bound verification, expiry/revocation checks | Local verification/gate tests; no trusted artifact service or route wiring |
| T04 | Unauthorized or replayed action | Exact-scope grants, one-time approval ticket, replay protection | Local policy/ticket primitives; no end-to-end live executor |
| T05 | Approval laundering or self-approval | Separate approver, authenticated ticket issuer, immutable scope | Local callback contract; no configured identity/governance provider |
| T06 | Malicious code escapes runner | Hardened isolation, microVM/host boundary, daemon cleanup, independent red team | Docker command unit tests only; hostile-code execution not tested |
| T07 | Message interception/tampering/replay | Authenticated encryption, secure key exchange, peer TLS, replay state | Local AES-GCM and signed-envelope tests; no live key exchange/TLS transport |
| T08 | Federation enumeration or malicious peer | Peer trust, visibility, quotas, signed records, revocation propagation | Local controls; no distributed federation or transparency log |
| T09 | Memory disclosure, poisoning or retention failure | Encryption, source provenance, ACL, secret filtering, deletion verification | Local AES-GCM prototype; no KMS, semantic index, backup deletion proof |
| T10 | Prompt injection or unsafe tool call | Treat model output as untrusted, schema validation, policy gate, human approval | Tool proposals only; no end-to-end prompt-injection evaluation |
| T11 | Malicious/low-quality specialist synthesis | Independent evidence verification, disagreement escalation | Adapter-based local checks; no calibrated verifier/benchmark |
| T12 | Unsafe self-modification | Immutable proposals, independent evaluation, separate approval, rollback | Local records only; no live mutation path exists |
| T13 | External/physical harm | Explicit scopes, operator consent, hardware interlocks, emergency stop | Simulation-only module; no real-world connector |
| T14 | Local database tampering or loss | Encryption, backups, external anchoring, restore drills | Local SQLite; no tamper-proof external log or disaster recovery proof |
| T15 | Dependency compromise / CI supply-chain attack | Pinned dependencies/actions, SBOM, vulnerability scan, signed build provenance | Not yet independently reviewed; CI workflow/dependency review outstanding |
| T16 | Denial of service / resource exhaustion | Rate limits, bounded payloads, quotas, concurrency limits, monitoring | Some local bounds; distributed rate limits and operational telemetry absent |

## Mandatory release-blocking conditions
- Replace shared bearer-token/client-selected workspace authority with a real server-side identity provider and tenant resolver.
- Integrate the verified action gate with all consequential HTTP and worker entry points.
- Demonstrate revocation during a running job and cancellation/cleanup at the execution boundary.
- Validate hostile-code isolation independently; Docker sharing the host kernel is insufficient evidence.
- Implement secure key agreement, TLS peer authentication and multi-node replay/revocation behavior before enabling network federation.
- Verify memory key custody, secret filtering, retention and deletion across backups.
- Perform prompt-injection, cross-tenant, authorization-bypass, replay, resource-exhaustion and supply-chain testing.
- Complete independent penetration test and resolve all critical/high findings.
- Establish backup/restore, incident response, monitoring and operator runbooks.

## Validation plan
1. Unit tests for each security primitive and negative path.
2. Cross-module integration tests with trusted test identity, key, policy, evidence, approval and receipt adapters.
3. API-level tests proving tenant identity is server-derived, not client supplied.
4. Adversarial tests for forged manifests, stale evidence, replay, scope widening, confused deputy, prompt injection and storage tampering.
5. Container/microVM escape and resource-exhaustion testing by qualified independent reviewers.
6. Multi-node federation/transport conformance and revocation propagation tests.
7. Dependency/SBOM review, secret scan, vulnerability scan and reproducible build review.
8. Independent penetration test and signed findings/closure evidence.

## Explicit exclusions
This document does not claim the system is secure, production-ready, generally intelligent, conscious, or safe for autonomous consequential execution. It records risks and evidence gaps so they cannot be mistaken for completed validation.
