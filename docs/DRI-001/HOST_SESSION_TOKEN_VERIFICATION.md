# Host-Issued Session Token Verification

## Purpose

The trusted runtime adapter needs a concrete, auditable way for a host
application to prove the authenticated subject and workspace. This increment
adds a dependency-free HS256 JWT verifier for host-issued sessions.

## Required host contract

The host must authenticate the user and issue a short-lived JWT containing:
- `iss`: configured identity issuer
- `aud`: XParallel API audience
- `sub`: authenticated subject
- `workspace_id`: workspace authorized for that subject
- `exp`: expiry timestamp
- optional `nbf`: not-before timestamp

The verifier checks the HS256 signature in constant time, algorithm, issuer,
audience, expiry, not-before, subject, and workspace format. Signing secrets
must be high-entropy (at least 32 bytes), stored server-side, and never sent to
the browser. Use HTTPS and short token lifetimes.

## Evidence

Unit tests cover valid tokens, signature tampering, expiration, not-before,
issuer/audience mismatch, algorithm rejection, invalid workspace, missing
expiry, weak secrets, and malformed input.

## Limitations / deployment gate

This code verifies tokens; it does not authenticate users or issue tokens.
No identity provider is selected or configured. The HTTP server has not been
wired to this verifier, and existing XP_TOKEN routes remain unchanged. HS256
requires secure secret distribution/rotation between the host issuer and API.
Before route integration, choose the host identity issuer, configure distinct
per-environment secrets and issuer/audience values, and test real host-issued
sessions. Do not treat this verifier alone as production authentication.
