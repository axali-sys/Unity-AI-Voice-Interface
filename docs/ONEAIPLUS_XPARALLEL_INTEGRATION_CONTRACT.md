# Oneaiplus ↔ XParallel Integration Contract

Status: implementation contract for the Oneaiplus server adapter. This document does not enable a live connection.
Scope: server-to-server integration between the Oneaiplus TanStack Start application and the XParallel Python service in this repository.

## 1. Integration boundary

Oneaiplus is the canonical user-facing workspace. Its TanStack Start server owns the signed-in user session, workspace authorization, UI state and product navigation. XParallel remains the governed infrastructure service.

The browser calls Oneaiplus same-origin server functions/routes. Oneaiplus server code calls XParallel. The browser must not call private XParallel routes directly and must never receive XP_TOKEN or any other host credential.

TanStack Start supports server-only functions for app-internal RPC and server routes for explicit HTTP APIs. The integration should use a server function for UI-initiated operations and a server route only where a stable external HTTP endpoint is required. Authentication must be enforced inside the server handler, not only in route navigation or client UI.

## 2. Configuration

Server-only environment variables in the Oneaiplus hosting environment:

- `XPARALLEL_BASE_URL`: HTTPS origin of the XParallel service, no path suffix.
- `XP_TOKEN`: private XParallel bearer token. Store only as a server secret. Never prefix it with `NEXT_PUBLIC_`, expose it to client loaders/components, serialize it, log it or return it in errors.
- `XPARALLEL_TIMEOUT_MS`: optional bounded request timeout; recommended default 5000 ms for diagnostics and 15000 ms for bounded data operations.

Public, non-secret configuration may include a display label or feature flag. The service URL is not a credential, but should still be read by server code for private operations.

## 3. Read-only diagnostics (no bearer token)

These endpoints are intended for basic availability and capability discovery:

| Method | Path | Purpose | Expected response |
|---|---|---|---|
| GET | `/public/health` | Health/version/network and sandbox availability | `status`, `network`, `version`, `sandbox_available` |
| GET | `/public/xparallel/access` | Gateway identity and advertised capabilities | gateway manifest |
| GET | `/public/system` | Omni/UnitAI system manifest | system manifest |

Important: in the current server implementation these public endpoints enforce `XP_PUBLIC_ORIGINS` when a browser Origin header is present. A server-to-server request without an Origin header is not the same as a browser CORS request. The Oneaiplus server adapter should make the request server-side and must not weaken the XParallel origin policy just to make a browser call succeed.

The unauthenticated `/health` endpoint is a process-level health check; prefer the `/public/health` response for the Oneaiplus module status display.

## 4. Authenticated server-to-server operations

The current XParallel handler checks its private bearer-token authorization before processing these routes. The Oneaiplus server adapter must send:

```
Authorization: Bearer <XP_TOKEN>
Content-Type: application/json
Accept: application/json
```

Useful existing routes include:

| Method | Path | Purpose | Oneaiplus module |
|---|---|---|---|
| POST | `/chat` | Provider-backed conversation | Assistant (provider availability must be explicit) |
| GET/POST | `/conversations` | Workspace conversation persistence | Assistant / Jellybox |
| GET/POST | `/memory` and memory routes | Workspace memory operations | Jellybox |
| GET/POST | `/repair/jobs` | Plan-only repair jobs and history | AI Repair Shop |
| GET | `/graph` | Workspace knowledge graph | Builder / Parallel Intelligence |
| POST | `/agent/plan` | Planning response | Omni Engine (plan only) |
| POST | `/route` | Intent routing | Omni Engine |
| POST | `/build` | Build plan | Builder (does not deploy) |
| GET | `/execution/health` | Sanitized recovery health | XParallel operations (only if trusted JWT host is configured) |

The exact request/response schemas must be confirmed from the corresponding route implementation before wiring each operation. Do not infer undocumented fields from UI labels.

## 5. Execution and governance remain separate

The Oneaiplus integration must not expose private execution controls as ordinary chat actions.

- `/execute` requires the configured explicit approval header and is not a generic Oneaiplus chat endpoint.
- The newer `/execution/intents`, `/execution/approve`, `/execution/run` and `/execution/recover` routes remain unavailable unless trusted JWT identity and the trusted execution host are configured.
- Governance grant/revocation routes remain unavailable unless the trusted identity verifier and governance adapters are configured.
- Never report execution or revocation as operational solely because the UI switch exists.
- Revocation applies to XParallel authorization for unauthorized or no-longer-authorized work. It must not affect ordinary assistant conversations.

The Oneaiplus UI should initially expose read-only diagnostics and planning. Any future execution workflow requires separate authorization, explicit human approval, expiry, resource limits, runtime revocation checks and evidence receipts.

## 6. Status vocabulary

Use these distinct states in Oneaiplus:

- `not_configured`: base URL or required server secret is absent.
- `unreachable`: request timed out or host could not be reached.
- `origin_blocked`: XParallel returned 403 `origin_not_allowed`; diagnose server/browser origin handling rather than opening all origins.
- `unauthorized`: private request returned 401; do not reveal token details.
- `host_unavailable`: service returned 5xx.
- `available_read_only`: diagnostics succeeded but no private operation has been tested.
- `authenticated`: a protected, non-destructive route succeeded with the user's server-authorized workspace scope.
- `provider_unavailable`: chat provider missing or failed; do not fabricate an answer.
- `approval_required`: operation is gated and no execution occurred.
- `verified`: only after the exact operation's runtime test and evidence check passed.

Never turn a successful public health response into a claim that private execution, AI inference, governance or worker execution is ready.

## 7. Workspace and identity binding

- Derive the user ID, role and workspace ID from the verified Oneaiplus server session.
- Never trust actor, owner, role or workspace fields supplied only by the browser.
- When XParallel is in JWT mode, use a trusted short-lived session JWT with the configured issuer and audience. Do not forward a raw Supabase access token unless the XParallel verifier is explicitly configured to validate that exact token format and issuer.
- Do not silently fall back from JWT mode to a shared owner token for user-scoped actions.
- Until the identity bridge is implemented and tested, limit integration to read-only public diagnostics and clearly mark private workspace actions as not connected.

## 8. Minimum acceptance tests

1. Missing `XPARALLEL_BASE_URL` yields `not_configured` without throwing a page error.
2. Missing `XP_TOKEN` prevents private calls and does not prevent read-only public diagnostics.
3. A public health request returns only the sanitized health payload.
4. A 403 origin error is surfaced as `origin_blocked`, not mislabeled as offline.
5. A 401 private response is surfaced as `unauthorized` without logging credentials.
6. Timeout and 5xx responses are bounded and mapped to unavailable states.
7. Browser bundles, rendered HTML, client network responses and logs contain no `XP_TOKEN`.
8. Browser-supplied workspace/actor/role cannot override verified session claims.
9. Chat failure due to provider configuration is reported honestly; no synthetic assistant response is returned.
10. No request to `/execute` or private execution routes is made by read-only diagnostics or ordinary chat.

## 9. Rollout sequence

1. Add a server-only XParallel diagnostics adapter in Oneaiplus.
2. Test read-only diagnostics using a mock HTTP server and an integration environment.
3. Add one authenticated, non-destructive private route only after the identity bridge is validated.
4. Add workspace memory and conversation persistence with cross-workspace isolation tests.
5. Add planning/routing and plan-only repair operations.
6. Integrate provider-backed chat only after a provider is configured and a live call succeeds.
7. Treat governance and execution as a separate security milestone with independent approval.

No Render/Vercel connection, deployment, production configuration change, credit purchase or main-branch merge is part of this contract.
