# Operational execution host-service boundary

## What this milestone adds

`xparallel/execution_host_services.py` provides a fail-closed composition
boundary for the approved execution worker. It requires explicit host adapters
for authoritative payload retrieval, artifact resolution, current policy
evidence, actual resource measurement, durable evidence storage, and signed
receipt recording.

The boundary validates:
- artifact SHA-256 against the immutable approved intent;
- current policy decision and non-empty grant/evidence identifiers;
- a complete set of non-negative integer resource measurements;
- measured wall time, memory, output and process count against approved limits;
- explicit durable-storage acknowledgement and unique evidence references.

## What this does not claim

The adapter contract is not itself a resource meter, object store, identity
provider, signing-key manager, or Docker host. Those remain injected trust
roots and must be implemented and independently verified in the selected
runtime environment. A `durable: true` response is an assertion from the
configured storage adapter, not cryptographic proof of durability.

The worker is not connected to a public or private HTTP route by this change.
No route is activated until a real host authenticator, authorization adapters,
artifact store, resource meter, evidence store, receipt signing key and
persistent storage are configured and integration-tested together.

## Operational release blockers

1. Select and configure a trusted host identity provider; JWT verification is
   currently opt-in and does not issue or authenticate user accounts.
2. Supply authoritative artifact storage and a runner-image digest pinned by
   the deployment.
3. Supply resource measurements from the actual container runtime, not from
   requested limits or runner self-report alone.
4. Supply durable evidence storage with immutable references and retention.
5. Supply protected signing-key management for receipts and verify signatures
   outside the worker process.
6. Exercise cancellation/revocation against a real supervised worker and
   prove process termination.
7. Only then enable a private API route under verified per-user identity,
   exact workspace binding, role authorization, one-time ticket consumption,
   rate limits and audit logging.

All current development remains isolated. No production route, deployment,
paid service, merge, DNS change or external execution was performed.
