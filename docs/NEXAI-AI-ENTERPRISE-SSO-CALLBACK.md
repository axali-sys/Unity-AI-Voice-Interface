# NexAI → AI Enterprise callback (development branch)

## Implemented

- `POST /api/auth/nexai/start` creates cryptographically random state and PKCE verifier/challenge, stores the verifier only in a signed HttpOnly cookie, and returns the authorization request data for the NexAI consent UI. The browser never receives the verifier.

- `GET /api/auth/nexai/callback` validates the one-time OAuth state cookie and state query parameter.
- The callback exchanges the authorization code with NexAI from the server, using the confidential client secret and PKCE verifier. The verifier is never returned to browser JavaScript.
- The NexAI HS256 assertion is verified for signature, algorithm, issuer (`nexai-platform`), audience (`axaliai-enterprise`), expiry, subject, workspace and role.
- AI Enterprise creates its own short-lived, signed, HttpOnly session cookie. NexAI's access assertion and NexAI session cookie are not exposed or reused.
- `GET /api/auth/session` returns only the authenticated user/workspace/role summary. `DELETE` clears the AI session cookie.
- All callback/session responses are non-cacheable. Cookies are HttpOnly and SameSite=Lax; Secure is enabled in production.

## Required server-only development configuration

- `AI_SESSION_SECRET`: random secret, at least 32 characters. Used only to sign AI Enterprise's own session and temporary OAuth state.
- `NEXAI_AXALIAI_IDENTITY_SECRET`: must match NexAI `NEXAI_AXALIAI_IDENTITY_SECRET`; at least 32 characters.
- `NEXAI_AXALIAI_OAUTH_CLIENT_ID`: defaults to `axaliai-enterprise`.
- `NEXAI_AXALIAI_OAUTH_CLIENT_SECRET`: dedicated confidential client secret, at least 32 characters.
- `NEXAI_AXALIAI_TOKEN_URL`: server-reachable NexAI token endpoint, e.g. the development backend's `/api/v1/integrations/axaliai/oauth/token`.
- `NEXAI_AXALIAI_REDIRECT_URI`: exact callback URI registered in NexAI's allow-list, e.g. `http://localhost:3000/auth/nexai/callback`.

Do not put any of these values in `NEXT_PUBLIC_*` variables or commit real values. No secrets have been generated, stored, or deployed by this change.

## Deliberate integration boundary / remaining work

This callback is the receiving half of the authorization-code flow. The NexAI consent page and AI Enterprise login-start route that create the signed state cookie and PKCE challenge are not yet implemented, so the browser flow is not end-to-end complete. NexAI's `/authorize` endpoint requires a real authenticated NexAI session and explicit consent; do not replace that with a fabricated `consent=true` request.

The AI session is not yet passed to XParallel. XParallel's enterprise adapter currently expects an `X-Enterprise-Identity` token with a subject/workspace/role signed by its configured identity secret. The next integration must mint a short-lived XParallel assertion server-side from the verified AI session, or use a dedicated trusted adapter. Until that is implemented and tested, keep chat on the existing preview-only workspace with memory disabled. Do not enable workspace memory merely because the AI session cookie exists.

No main-branch changes, merges, preview deployments, production deployments, or secret provisioning were performed.
