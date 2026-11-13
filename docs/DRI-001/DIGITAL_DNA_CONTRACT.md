# XParallel Digital DNA — Contract Specification (Draft 0.1)

Status: Proposed contract; not yet implemented or security-certified  
Workstream: DRI-001 / M2  
Development branch: `dri-001/xparallel-master-blueprint`

## 1. Purpose

Digital DNA is the portable, machine-readable declaration that describes a digital entity's identity, owner, declared capabilities, interfaces, permissions, provenance, runtime compatibility and lifecycle state.

It is a contract and discovery record, not proof that an entity is intelligent, trustworthy, safe, available or capable of performing every declared task. Each claim must be independently verified before it can authorize an action.

## 2. Design rules

1. **Identity is not capability.** A valid identifier proves only that a record/key is associated with an entity under a stated issuer and verification method.
2. **Declaration is not verification.** Every capability has a claim status and evidence references; unverified claims cannot authorize execution.
3. **Ownership is explicit.** The manifest identifies an owner/controller and the authority that issued or attested the record. Ownership disputes require a separate process.
4. **No secrets in DNA.** Never embed API keys, passwords, private keys, access tokens, recovery phrases or credential values. Use scoped credential references resolved by a trusted vault.
5. **Least privilege.** Permissions are explicit, scoped, time-bounded where practical, and deny by default.
6. **Versioned contracts.** Schema, protocol and capability versions are independently declared. Unknown major versions fail closed.
7. **Portable, not coupled.** Runtime/provider references are descriptive adapters; no provider is mandatory.
8. **Revocable.** Identity keys, capability claims, permissions and entity registrations can be suspended or revoked.
9. **Auditable.** Registration, updates, key rotation, permission grants, execution and revocation produce provenance events.
10. **Human control for consequential actions.** The manifest cannot grant itself additional authority.

## 3. Entity record structure

### 3.1 Identity
- `entity_id`: stable opaque identifier, assigned by an issuer; do not derive it from a mutable display name.
- `entity_type`: one of agent, service, tool, model, device, organization or composite.
- `display_name`: human-readable label, not a unique identity.
- `issuer`: registry/authority identifier that issued or accepted the identity.
- `created_at`, `updated_at`: RFC 3339 timestamps.
- `status`: pending, active, suspended, revoked or retired.

### 3.2 Ownership and control
- `owner.subject`: stable owner/account identifier in the issuer's namespace.
- `owner.controller`: optional operating controller distinct from legal/administrative owner.
- `owner.proof_ref`: reference to a separately stored verification record; never include identity documents or secrets in the public manifest.
- `owner.transfer_policy`: policy identifier governing transfer, if supported.

### 3.3 Compatibility
- `schema_version`: version of this manifest schema.
- `protocols[]`: protocol identifiers and supported versions.
- `interfaces[]`: interface name, version, transport, direction and contract reference.
- `runtime`: optional runtime family, version and provider-neutral adapter identifiers.

### 3.4 Capabilities
Each capability entry includes:
- stable `capability_id` and version;
- a concise purpose and input/output contract references;
- status: declared, under_review, verified, suspended or revoked;
- evidence references and verifier metadata;
- limits: resource ceilings, rate limits, allowed data classes and supported environments;
- required permission scopes.

Only `verified` capabilities whose evidence is current and whose permissions are granted may be considered for an execution plan. The executor must still enforce its own policy and validate the request.

### 3.5 Permissions
Permissions are requests or grants, never self-issued authority. Each grant identifies:
- subject entity;
- action and resource scope;
- grantor;
- validity interval;
- constraints and approval reference;
- revocation state.

A manifest's requested permissions have no effect until an authorized policy service records a grant.

### 3.6 Memory and data handling
Declare supported memory classes and data handling policies, including retention, export, deletion, encryption-at-rest claims, residency and permitted processing. These are claims that require evidence and policy review; the manifest must not contain memory contents or personal data.

### 3.7 Provenance and integrity
Include a manifest digest/signature envelope in the registry layer, not a self-asserted trust score. Record signer key ID, algorithm, signature, signing time and prior manifest digest. Key trust, signature verification and revocation are registry responsibilities.

## 4. Registration and lifecycle

1. **Submit:** owner submits manifest and proof references over an authenticated channel.
2. **Validate:** validate JSON Schema, identifier namespace, version compatibility, size limits and required fields.
3. **Verify control:** verify the owner's authority and possession/control of the signing key using a challenge-response flow.
4. **Review claims:** capability evidence is evaluated separately; unsupported claims remain declared or under_review.
5. **Register:** registry creates a stable entity record and records an audit event.
6. **Discover:** discovery returns only permitted metadata and filters by status, protocol, verified capability and policy.
7. **Connect:** establish a mutually authenticated session and negotiate protocol versions.
8. **Authorize:** policy engine checks subject, action, resource, context, expiry, quotas and approval requirements for every action.
9. **Operate:** runtime validates inputs/outputs, enforces limits, records provenance and supports cancellation.
10. **Update:** submit a new immutable manifest version; retain previous digest and verification history.
11. **Rotate/revoke:** revoke compromised keys or capability claims; invalidate affected sessions and grants.
12. **Retire:** preserve minimum audit metadata under retention policy while disabling new work.

## 5. Trust and execution boundaries

- Registry status is not a security certification.
- A signed manifest proves integrity and signer-key possession, not truth of its content.
- A capability verifier should publish what was tested, environment, version, date, result and limitations.
- A runtime must not execute code merely because a manifest advertises a capability.
- All tool and network access is mediated by policy, sandbox, quotas and audit.
- Untrusted entity content is data, never executable policy or trusted instruction.
- Entity-to-entity messages require authenticated sender, schema validation, replay protection and size/rate limits.
- Consequential actions require a separately recorded approval from an authorized human or policy authority.
- Self-modification must be staged, tested, signed, reviewable and reversible. It cannot rewrite its own identity, permissions or trust record.

## 6. Minimum conformance tests

A first implementation is not conformant until automated tests cover:
1. missing/invalid identifiers and unsupported schema versions rejected;
2. duplicate registration handled idempotently;
3. owner challenge failure rejected;
4. signature mismatch and revoked key rejected;
5. unverified capability excluded from executable discovery;
6. expired, out-of-scope and revoked grants denied;
7. cross-workspace/entity data leakage denied;
8. protocol mismatch fails closed;
9. replayed message rejected;
10. oversized/rate-exceeding request rejected;
11. manifest update preserves prior digest/history;
12. revocation disables new work and invalidates applicable sessions;
13. audit event records actor, action, target, decision and correlation ID;
14. no secrets appear in serialized manifests, API responses or logs;
15. a simulated runtime failure cannot bypass approval or quota checks.

## 7. Deliberate non-goals for draft 0.1

This contract does not implement distributed consensus, blockchain identity, autonomous ownership transfer, a global trust score, a public marketplace, payment/settlement, self-replicating agents, unrestricted internet access or unsupervised self-modification.

## 8. Implementation sequence

- M2.1: schema and deterministic validation.
- M2.2: local SQLite registry prototype with workspace isolation and immutable manifest revisions.
- M2.3: owner/key challenge and signature verification using maintained cryptographic libraries.
- M2.4: capability evidence and verifier records.
- M2.5: permission grants, expiry and revocation integration.
- M2.6: authenticated protocol negotiation and message envelope.
- M2.7: conformance/security tests and threat-model review.

All work remains on the isolated DRI branch. No main merge, production deployment, paid service, or external identity issuance is part of this milestone.
