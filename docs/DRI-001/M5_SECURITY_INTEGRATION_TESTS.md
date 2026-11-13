# DRI-001 — M5 security integration test evidence

Status: Test-only composition evidence; not production integration.

## Added test

`tests/test_dri_security_integration.py` composes three independently tested modules:

1. `EntityGovernanceRegistry` — owner requests an exact-scope grant and a separate governance principal approves it.
2. `CapabilityVerificationLab` — a verifier runs a trusted-plan test against an artifact digest.
3. `VerifiedEntityActionGate` — an authenticated caller is allowed only when the exact artifact has current passing evidence and the governance registry returns an active matching grant.

The integration suite covers:
- Pending grant is denied; separately approved grant plus verified artifact and exact scope is allowed.
- Revoked grant is denied.
- Failed capability evidence is denied even with an approved grant.
- Artifact digest change invalidates prior evidence.
- Unauthenticated callers are denied.

## Test boundary

All identity, governance-authority, trusted-plan and isolated-runner adapters are explicit test doubles. The test proves local module composition and denial behavior only. It does not prove production authentication, route-level enforcement, genuine sandbox isolation, distributed storage, or a real human approval workflow. It does not connect the gate to any public or private HTTP execution route.

## Remaining M5 blockers

- Trusted production identity/session provider and server-side workspace resolution.
- Route-level enforcement immediately before execution, including approval tickets and runtime revocation checks.
- Real isolated execution adapter with independently validated hostile-code isolation.
- Durable transactional storage and signed execution receipts.
- Encrypted distributed transport, federation and multi-node revocation.
- Independent security review, penetration testing, dependency/SBOM review and operational recovery tests.

No merge or deployment is performed.
