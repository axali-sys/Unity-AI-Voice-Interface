# OneAI Hybrid Free Access Hub — implementation note

## Goal
Route tasks across local open-source models and legitimate free cloud tiers,
while keeping paid provider calls disabled unless explicitly enabled and
approved. This is an additive development-branch feature for the existing
OneAI/XParallel repository.

## Implemented in this branch
- `xparallel/free_access_hub.py`: deterministic local-first provider policy.
- `xparallel/provider_catalog.py`: environment-backed provider catalog. It
  exposes provider IDs/kinds/configuration only, never keys or endpoint URLs.
- `xparallel/hybrid_chat.py`: opt-in Ollama chat adapter, with optional
  OpenAI-compatible free-cloud fallback only when an operator explicitly
  configures it and sets its status to `available`.
- `GET /providers`: authenticated provider directory.
- `POST /provider/route`: authenticated routing decision endpoint. This is
  a decision endpoint, not a command to execute a provider request.
- Existing authenticated `POST /chat` uses the hybrid adapter only when
  `XP_HUB_ENABLED=true`; otherwise the legacy chat path remains unchanged.
- Next.js `/api/providers` proxies provider metadata server-side using
  `XP_TOKEN`; the workspace shows configured provider status and does not
  expose backend credentials.
- The chat UI can display the provider/model returned by the backend.

## Configuration (server-side only)
- Set `XP_HUB_ENABLED=true` to opt into the hybrid chat adapter.
- Local Ollama: set `XP_HUB_LOCAL_URL` to a local HTTP endpoint (for example
  `http://localhost:11434`) or trusted HTTPS endpoint, and set
  `XP_HUB_LOCAL_MODEL` to an installed model name.
- Optional free-cloud fallback: set `XP_HUB_FREE_PROVIDER_URL`,
  `XP_HUB_FREE_PROVIDER_MODEL`, and `XP_HUB_FREE_PROVIDER_API_KEY`; then set
  `XP_HUB_FREE_PROVIDER_STATUS=available` only after independently verifying
  provider access and remaining quota, and set
  `XP_HUB_ALLOW_FREE_FALLBACK=true` to opt into fallback.
- Do not put provider secrets in frontend variables or return them from APIs.
- Do not expose a local Ollama port directly to the public internet. A hosted
  backend cannot reach a model on a user's device unless a separately secured
  bridge or private network is configured.

## Cost and approval guardrails
- Local inference has no per-request model API charge but still needs hardware,
  electricity, storage, and model downloads.
- A provider's configured identity does not prove live availability or free
  quota. The directory intentionally reports status as unknown; routing does
  not select unknown providers.
- The hybrid chat adapter does not invoke paid providers.
- The separate policy supports paid selection only with server-side enablement
  and a separate approval token/header; a client-supplied boolean alone is not
  sufficient.
- If no eligible provider exists, return an honest configuration/availability
  error. Do not bypass login, paywalls, licence checks, quotas, or access rules.

## Verification status
GitHub Actions passed on the current development branch for Python compilation,
routing-policy tests, provider-catalog secret-safety tests, hybrid-chat tests,
OneAI interface safety, memory, planner, and conversation-store checks. Provider
requests in tests are mocked; live model inference and real free-tier quota
verification have not yet been performed.

## Remaining before merge
1. Configure Ollama in a suitable private runtime or secured local setup.
2. Verify local inference and any free-cloud fallback with real credentials and
   quota checks in a non-production environment.
3. Confirm frontend preview behavior and inspect Vercel rate-limit failures.
4. Run end-to-end checks for chat, memory, workspace isolation, and provider
   error handling.
5. Review the draft pull request; do not merge or promote to production without
   explicit approval.
