# XParallel Parallel World + AI Memory integration

## What this change adds
- `public/xparallel.html`: mobile-first Parallel World workbench and server-connected AI Memory UI. Existing `public/index.html`, route handlers, and workflows are left intact.
- `xparallel/memory_service.py`: retrieves relevant records from the existing SQLite memory vault and calls a configured OpenAI-compatible chat-completions endpoint for a grounded summary.
- `xparallel/server.py`: adds an authenticated `POST /memory/summarize` endpoint; existing route paths are retained.

## Parallel World model
XParallel's intended architecture is: human goal -> intent/plan -> isolated workspace -> bounded execution -> tests and evidence -> human review -> explicit approval -> real-world transfer. It is designed to extend through adapters for software repositories, operating systems, cloud infrastructure, data pipelines, and other platforms. It does not mean every arbitrary program/job is already supported. Each adapter needs explicit permissions, test fixtures, sandbox limits, evidence, rollback, and approval gates.

The UI's `Create AI plan` action uses the existing `/build` API. `Run isolated experiment` uses the existing `/experiment` API and accepts only a file manifest whose file contents are Base64 strings. The current runner is Docker-based and can report blocked when Docker is unavailable. The experiment route does not deploy to production. The separate `/execute` route retains its existing approval-token gate.

## AI Memory service
- The source text remains stored in the existing memory vault; summaries are derived and never replace source records.
- Retrieval uses the existing workspace-scoped lexical search. Semantic embeddings can be added behind this interface later.
- `POST /memory/summarize` requires the existing bearer-token authentication and returns a 503 when provider configuration is missing or unavailable; it does not pretend a heuristic is an AI summary.
- Set server-side `XP_AI_API_KEY`, `XP_AI_MODEL` (default `gpt-4o-mini`), and optionally `XP_AI_CHAT_COMPLETIONS_URL`. The endpoint must use HTTPS. Never put provider keys in the HTML or browser storage.
- Browser bearer token is held in `sessionStorage` for this tab only. Use HTTPS, a narrowly scoped token, and clear it on shared devices. The current backend uses a shared `XP_TOKEN`; multi-user production needs identity-backed workspace authorization rather than trusting a caller-supplied workspace ID.

## Persistence and production security
- Configure `XP_MEMORY_DB` to a durable, writable volume or replace the SQLite adapter with managed Postgres/SQLite-compatible storage before relying on persistence in ephemeral/serverless hosting.
- Back up source records and test restore. Memory deletion does not purge exported backups.
- Add per-user/workspace authorization, rate limits for private authenticated routes, audit records for memory writes/deletes, retention controls, and secret redaction before production.
- Do not store passwords, access tokens, or sensitive secrets as memories. Treat retrieved memory as untrusted prompt input.
- Docker execution must remain network-disabled and resource-limited. Keep real-world changes behind review, explicit approval, and rollback plans.

## Verification checklist
1. Python syntax/import checks for `xparallel/server.py` and `xparallel/memory_service.py`.
2. Unit tests for save/list/search/dedup/forget, provider success, provider missing key, malformed provider response, and workspace separation.
3. API tests for unauthorized access, invalid payloads, retrieval limits, and summarization errors.
4. Browser test with a configured API, then test no token, invalid token, missing AI provider, and unavailable Docker.
5. Confirm existing public endpoints, execution approval gate, GitHub workflows, and deploy configuration are unchanged.
6. Configure persistent storage and provider secrets in the deployment environment before enabling production use.

This branch is a proposed integration. It does not imply deployment, provider configuration, persistent-volume setup, or production verification.
