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
