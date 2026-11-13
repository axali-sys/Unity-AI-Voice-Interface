# Private JWT execution API adapter

`xparallel/execution_http_api.py` provides a framework-independent private
API adapter for execution intent creation, separate approval, one-time ticket
consumption, and pending receipt recovery.

The adapter:
- accepts only verified host JWT claims supplied by the HTTP layer;
- derives workspace and actor from those claims, never from request JSON;
- applies role gates (owner/operator request, owner/admin approval, operator
  execution and recovery);
- requires exact request field sets and rejects caller-supplied identity fields;
- requires the trusted control plane and execution host services to share the
  same approval registry;
- returns the one-use ticket only in the approver's response.

The approval registry still enforces requester/approver separation and the
worker enforces current entity, grant, artifact and verification checks.
This adapter does not create host adapters, signing keys, storage, resource
metering, or an identity provider.

## Server integration boundary

The HTTP server now dispatches four private POST paths: `/execution/intents`,
`/execution/approve`, `/execution/run`, and `/execution/recover`. Dispatch is
fail-closed: it requires JWT mode, a configured verifier, and an explicitly
injected `ExecutionHTTPAPI` instance. With no host bootstrap, requests return
`trusted_execution_host_not_configured`; in legacy shared-token mode they
return `trusted_execution_identity_unavailable`. No default execution adapters
are created, and these routes are not public.


## HTTP dispatch verification

`tests/test_execution_http_routes.py` exercises the actual server dispatch
helper with injected test adapters. It verifies that unrelated paths are not
captured, legacy shared-token mode is denied, missing host bootstrap is denied,
all four JWT-only routes dispatch with the verified workspace claims, and
authorization failures map to safe HTTP responses. These are in-process tests;
they do not establish a live network listener, configured identity provider,
or production host integration.


## Independent host-session revalidation

The HTTP layer verifies the bearer token to obtain issuer-signed role claims.
The private execution adapter forwards the original bearer token—not a
caller-constructed principal dictionary—to the approval registry and worker.
The registry's configured host authenticator must independently validate that
token and return the authoritative subject and workspace. The host can use
the same `HS256SessionVerifier` instance (or an equivalent verifier configured
with the same issuer, audience, key and clock policy) as its authenticator. This prevents the
execution control plane from treating an ordinary claims dictionary as a
session credential.

This is still a host integration contract: the host must configure its
authenticator to validate the same issuer, audience, expiry and signing key.
No identity provider or live host authenticator is configured by this branch.


## Signed-session integration test

`tests/test_execution_http_jwt_binding.py` composes the actual HS256 verifier,
trusted execution control plane, approval registry and HTTP API adapter. It
proves that a signed owner token can request an intent, a separately signed
admin token can approve it, and a tampered token is rejected again at the
registry boundary even when valid-looking claims are separately supplied.
The test uses in-memory registries and a fake worker; it does not run Docker or
establish a production identity-provider connection.


## End-to-end signed execution lifecycle test

`tests/test_execution_http_jwt_binding.py` now includes an integrated test
that creates an intent with a signed owner session, obtains approval from a
separate signed administrator session, and executes with a distinct signed
operator session. It composes the actual approval registry, host-services
adapter, approved worker, signed receipt ledger and evidence adapter. The test
asserts the final job state, immutable evidence reference, signed receipt and
receipt-chain verification.

The runner, policy evidence, resource measurement, evidence persistence and
receipt signing are deterministic test adapters. This validates the complete
software lifecycle and adapter wiring; it does not prove Docker isolation,
real host resource metering, external durable storage, or production identity
infrastructure.


The same end-to-end test also starts a second approved execution, revokes the
entity's permission from inside the test runner, and verifies that the worker
downgrades the nominally successful runner result to a blocked outcome before
the terminal receipt is committed. The test confirms the receipt chain remains
valid for both execution records.
