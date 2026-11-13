# Opt-in HTTP JWT Identity Enforcement

## Route behavior

The XParallel HTTP server now supports an explicit `XP_AUTH_MODE=jwt` mode.
In this mode every private GET/POST route authenticates the bearer token using
`HS256SessionVerifier`. Missing verifier configuration, malformed tokens,
invalid signatures, expired sessions, and claim mismatches fail closed.

Required server-side settings:
- `XP_AUTH_MODE=jwt`
- `XP_SESSION_JWT_SECRET` (at least 32 bytes of high-entropy secret material)
- `XP_SESSION_JWT_ISSUER`
- `XP_SESSION_JWT_AUDIENCE`

The host identity issuer must sign claims `sub`, `workspace_id`, `role`,
`iss`, `aud`, `exp`, and optionally `nbf`. Roles are limited to owner,
admin, operator, and viewer. Missing role defaults to viewer. Role is taken
only from the verified token, not request data.

After authentication, POST request bodies and GET query parameters are bound
to the signed subject/workspace. Caller-supplied actor or workspace values
must match exactly; mismatches and duplicate query identity parameters are
rejected. The actor and workspace used by downstream workspace-aware handlers
are derived from the verified claims.

## Compatibility

The default remains `XP_AUTH_MODE=legacy` to avoid silently breaking existing
deployments. Legacy mode still uses the shared `XP_TOKEN` and is not equivalent
to per-user authentication. Unknown auth-mode values fail closed for private
routes. Public routes retain their separate origin/rate-limit behavior.

## Evidence and limitations

Unit tests cover bearer parsing, claim binding, role allowlisting, actor
spoofing, cross-workspace access, and duplicate query identity parameters.
The JWT verifier has separate cryptographic tests.

No host issuer has been selected or configured, and no deployment environment
has been changed. JWT mode has not been enabled on any live service. The
existing `/execute` handler still uses its legacy execution/approval flow and
has not been connected to the verified action gate or one-time execution
tickets. This increment therefore demonstrates code-level route enforcement
when correctly configured, not a production identity rollout.
