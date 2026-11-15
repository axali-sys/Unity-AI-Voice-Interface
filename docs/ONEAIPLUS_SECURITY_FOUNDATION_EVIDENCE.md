# Oneaiplus Security Foundation Evidence Note

Date: 2026-11-15  
Repository: `axali-sys/Unity-AI-Voice-Interface`  
Branch: `oneaiplus/unification-foundation-2026-11-14`

## C072 — UIDaaS / identity foundation (Partial)

Source inspected:
- `xparallel/session_jwt.py`
- `xparallel/http_identity.py`

Test coverage:
- `tests/test_session_jwt.py`
- `tests/test_http_identity.py`

The host-session verifier validates HS256 signatures, configured issuer and audience, expiry/not-before, non-empty subject, workspace identifier shape and recognized role values. HTTP identity binding derives actor/workspace from verified claims and rejects caller-supplied identity overrides.

Boundary: XParallel verifies tokens issued by a trusted host. This repository module does not itself authenticate a user, issue identity credentials, or prove the host's deployed issuer/audience/signing secret is configured correctly. A complete cross-product UIDaaS and multi-tenant identity service is not established by these modules.

## C075 — Permission Engine (Partial)

Source inspected:
- `xparallel/authz.py`

Test coverage:
- `tests/test_authz_audit.py`

The role/action policy primitive is deny-by-default, rejects unknown and non-string role/action values, and exposes immutable role/action tables. Tests cover role boundaries, unknown actions and mutation attempts.

Boundary: this is a role-level primitive only. Its own module documentation requires callers to authenticate identity and apply resource/workspace-specific policy separately. It is not yet a complete policy decision/enforcement service across Oneaiplus modules.

## CI gate

The XParallel GitHub Actions workflow explicitly runs the role authorization and HTTP identity suites. This note adds an explicit workflow step for `tests/test_session_jwt.py`; the workflow change is at commit `757db639d5089218817a97165835a13ced4df3b7`. The JWT test step is pending CI confirmation for that commit and must not be represented as passed until the run completes.

## Required next evidence

1. Confirm the explicit JWT verifier test step passes in CI.
2. Exercise a host-issued token from an isolated development identity provider without exposing signing secrets.
3. Verify deployed issuer/audience/key configuration and secret rotation on a non-production host.
4. Add resource/action/workspace policy enforcement tests at actual route boundaries, including caller override and cross-workspace denial.
5. Demonstrate account lifecycle, credential revocation and audit reconstruction end-to-end.

No production deployment, secret rotation, default-branch merge or paid resource activation is included in this work.
