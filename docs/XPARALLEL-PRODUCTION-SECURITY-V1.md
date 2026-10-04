# XParallel Production Security V1

XParallel now separates identity from authorization. A hosting layer may authenticate
the caller, while the authorization module makes explicit role decisions:

- viewer: read/search
- operator: create solutions
- admin: verify/billing
- owner: deployment approval

Security-sensitive operations can produce tamper-evident audit events.

Before enterprise production, connect this boundary to a real identity provider,
managed PostgreSQL, centralized audit storage, secret rotation, shared rate-limit
storage, payment processor, and independent security testing.

No identity provider, payment processor, or deployment credential is fabricated by
this prototype. The approval gate remains explicit.
