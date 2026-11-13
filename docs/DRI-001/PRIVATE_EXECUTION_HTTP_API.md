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

The adapter is not enabled by default and is not a public endpoint. A host
must explicitly construct it with real trusted adapters and inject it into
the HTTP server. Until that is done, the server must fail closed and report
execution unavailable. Legacy shared-token authentication is not sufficient
for this API. No route is enabled by this module alone.
