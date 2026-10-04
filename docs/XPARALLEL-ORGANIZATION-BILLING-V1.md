# XParallel Organization & Billing V1

XParallel includes a tenant-oriented organization/member model and a billing-contact boundary.

## Current V1 boundary
- Organization IDs provide a canonical tenant identifier for billing and future resource scoping.
- Roles are owner, admin, operator and viewer.
- Billing is invoice-preview/metering only; payment capture is intentionally not implemented.
- Billing email is supplied by the runtime environment variable XP_BILLING_EMAIL.
- Bank account information is never stored in source control or application configuration.

## Important production limitation
The current HTTP server still derives request workspace scope from request data. The organization model is therefore a foundation, not yet a complete identity-enforced multi-tenant boundary. Before treating it as production isolation, connect a real identity provider and organization membership resolver, then derive organization/workspace scope from authenticated identity rather than caller-supplied workspace IDs.

## Production sequence
1. Merge and verify this foundation.
2. Connect managed PostgreSQL and migrations.
3. Connect a real identity provider and organization membership.
4. Enforce organization/workspace scope in every solution, graph, audit and billing path.
5. Connect a regulated payment processor or official bank API.
6. Configure production secrets through the hosting secret manager.
7. Deploy and run smoke/security tests.
