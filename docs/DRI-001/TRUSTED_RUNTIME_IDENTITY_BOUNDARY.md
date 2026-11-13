# Trusted Runtime Identity Boundary

## Purpose

This milestone adds a small adapter boundary between an HTTP/application host
and XParallel's entity authorization, execution approval, and receipt modules.
An opaque host session is passed to an injected authenticator. Only the
authenticator's server-side claims may establish the subject and workspace.

## Contract

- The host authenticator must return an authenticated claim set with a
  non-empty subject and a syntactically valid workspace identifier.
- Workspace identity is derived only from those trusted claims.
- A caller-supplied workspace, if present, is checked for exact equality; it
  can never select or override the authenticated workspace.
- The actor recorded by this adapter is the authenticated subject, not a
  request-body actor string.
- Missing, malformed, unauthenticated, mismatched, or unavailable identity
  dependencies fail closed with a permission error.

## Evidence

Unit tests cover trusted claim derivation, matching workspace consistency,
cross-workspace mismatch, anonymous/unknown sessions, malformed claims, and
authenticator failure.

## Explicit limitations

This is an adapter contract and test seam, not a production identity provider.
The current HTTP server still authenticates with a shared XP_TOKEN and still
has routes that accept caller-provided workspace/actor values. This adapter
has **not** been wired into those routes. No real sessions, OIDC/JWT validation,
role mapping, key rotation, CSRF protection, or production identity integration
are claimed. The execution route remains outside this trusted runtime boundary
and must not be treated as production-safe.

Next integration work requires selecting/configuring a real host-side verifier
and applying the trusted principal consistently to every private route before
enabling any entity execution entry point.
