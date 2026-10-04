# XParallel Organization & Billing V1

XParallel now has a tenant-oriented organization/member boundary and a billing-contact boundary.

## Production boundary
- Organization IDs scope solution, graph, audit and billing records.
- Roles are owner, admin, operator and viewer.
- Billing is invoice-preview/metering only; payment capture is intentionally not implemented.
- Billing email is supplied by the runtime secret/environment variable XP_BILLING_EMAIL.
- Bank account information is never stored in source control or application configuration.
- A real payment processor and managed database must be connected before charging customers.

## Release sequence
1. Merge and verify this layer.
2. Connect managed PostgreSQL.
3. Connect a real identity provider and organization membership.
4. Connect a payment processor.
5. Configure production secrets.
6. Deploy and run smoke/security tests.
