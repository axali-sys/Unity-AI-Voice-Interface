# Oneaiplus Public-Surface and Chat API Security Review

Date: 2026-11-15
Canonical project: c2232890-a16d-4289-b2f8-c8de6365a7b4
Inspected source ref: 3fac96efc001f394622301568f2f42417c08a87a
Review type: Read-only source inspection; no requests sent to the published app.

## Executive result
The published project is configured with public publish audience, while the application routes and server functions are intended to remain owner-only. Public hosting is not by itself a data breach: the authenticated route group performs a client-side Supabase user check and calls is_oneai_owner(), and the chat API independently validates a bearer token and calls the same database owner function. Server functions inspected elsewhere also use requireOwner middleware.
However, the public /api/chat route needs stronger request-shape and abuse controls before it should be considered robust for broader use.

## Verified access controls
1. Authenticated application routes are nested under src/routes/_authenticated/route.tsx. beforeLoad calls supabase.auth.getUser(), then is_oneai_owner(); failures sign out and redirect to /auth.
2. The /api/chat handler is outside the client route group, but independently requires a Bearer token, validates it with Supabase auth.getUser(token), then calls is_oneai_owner().
3. src/lib/owner.functions.ts wraps server functions in requireSupabaseAuth and the database is_oneai_owner() check.
4. The chat provider call is server-side; LOVABLE_API_KEY is not read by browser code.
5. The AI SDK provider options set store:false.

## Findings and risks

### 1. Chat request validation is shallow
src/server/chat.server.ts parses JSON and checks only that body.messages is a non-empty array of at most 100 entries. It then passes the messages to convertToModelMessages(). There is no explicit maximum request-body byte size, per-message text length, total text length, allowed role/part schema, or rejection policy for unsupported part types visible in this handler.
Risk: oversized or malformed authenticated requests may consume memory, provider tokens or processing time. The owner-only gate reduces the caller population but does not replace request validation.

### 2. No application-level rate or concurrency limit is visible
The inspected handler has no per-user rate limiter, concurrent-stream cap, daily token budget or request queue. Provider billing limits are not an application security control.
Risk: a stolen session or repeated owner requests can create unexpected AI spend or degrade service. This is especially important while the workspace has previously returned HTTP 402 for insufficient credits.

### 3. Public hosting metadata must not be confused with public data access
Lovable project metadata reports is_published=true and publish_audience=public. The reviewed application routes are owner-gated, but this audit did not perform unauthenticated HTTP penetration tests against every route, static asset, server function or storage policy.
Risk: do not describe the whole application as externally inaccessible solely because the authenticated route group is gated. Confirm every server endpoint and every database/storage policy independently.

### 4. Chat is intentionally not persisted
HomeChat states that messages clear when leaving the page. The UI uses in-memory useChat state and no conversation persistence call was found in the inspected component.
Risk: conversation continuity and recovery are not available. Do not imply chat history is saved until durable owner-scoped persistence and deletion controls exist.

## Recommended controls before wider use
1. Enforce a small request-body byte limit before JSON parsing; return 413 when exceeded.
2. Validate message objects with a strict schema: supported roles only, text parts only unless tools are explicitly approved, bounded part counts and bounded per-message/aggregate text lengths.
3. Apply server-side per-user rate limits, concurrent stream limits and a configurable hard spending/token budget. Fail closed when the limiter is unavailable.
4. Use provider timeouts and bounded output-token limits; propagate client cancellation and do not retry costly calls blindly.
5. Add redacted security audit events for denied requests, rate-limit decisions, provider status and request IDs. Never store bearer tokens or raw secret values.
6. Add adversarial tests for missing/invalid/expired token, non-owner, malformed JSON, wrong content type, oversized body, empty/101-message array, unsupported role/part, oversized text, rate limit, concurrent requests, provider 402/429/5xx and cancellation.
7. Perform an explicit route inventory and unauthenticated tests for every server function, API route and storage bucket. Confirm that published static assets contain no secrets or private data.
8. When chat persistence is implemented, use canonical owner-scoped tables and RLS; do not copy donor schemas without adapting to is_oneai_owner().

## Acceptance criteria
An owner-only UI is not sufficient. The API must independently authenticate and authorize every request, bound resource consumption, and pass negative tests. AI chat must not be labelled Operational until a real provider call succeeds and spending controls are verified.

## Non-actions
No network request was sent to the published application. No code, database, credentials, publication, visibility or billing state was changed. No deployment was triggered.