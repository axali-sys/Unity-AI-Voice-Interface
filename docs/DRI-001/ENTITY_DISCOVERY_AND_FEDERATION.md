# DRI-001 — Entity discovery and federation foundation

Status: partial local implementation; not a network federation service.

## Implemented
- Owner-authorized publication of Ed25519-signed discovery records using an active registered entity key.
- Public, allowlist and private visibility controls.
- Signed record verification against the issuer's active key before disclosure.
- Injected federation peer-trust policy.
- Protocol major-version compatibility checks and exact declared-capability filtering.
- Capability listings remain explicitly marked declared, never verified.
- Bounded result sizes, query rate limits, expiry and owner-authorized record revocation.
- Tests cover signatures, protocol compatibility, visibility, owner binding, revocation, wrong keys and rate limiting.

## Not operational / remaining
- Local SQLite only; no network registry endpoints, registry replication or cross-organization federation transport.
- No registry certificate/authority hierarchy, transparency log, key discovery bootstrap or trust-policy administration.
- No private/public search separation service, anti-correlation/privacy review or independent registry conformance suite.
- No distributed rate limits, query abuse telemetry or federated revocation propagation.
- No route integration with the host authentication service or encrypted transport.

A signed record proves control of the registered signing key and integrity of the record; it does not prove legal identity, truth of claims, capability verification, availability or permission to execute. Discovery is not authorization. Every action must still pass the server-side verified action gate.
