# M0 Repository Reconciliation — Initial Findings

**Repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Branch:** `enterprise/axaliai-completion`  
**Baseline PR:** #61 (draft; base `feat/elle-omni-knowledge-genome`)  
**Review date:** 2026-11-11  
**Scope:** Initial source-tree and high-risk path review. This is not yet a full 180-file code audit.

## Repository topology verified

- Repository default branch is `main`.
- PR #61 is open, draft, not merged, and compares `enterprise/axaliai-completion` against `feat/elle-omni-knowledge-genome`.
- The inspected branch tree contains 180 paths and includes the existing Next.js UI, Python XParallel backend, Vercel Python entrypoint, SQLite services, tests, and GitHub Actions workflows.
- Existing feature families include ƎllE lifecycle, Omni Knowledge Genome, Parallel Intelligence, provider catalog/hybrid chat, memory vault, conversation history, roaming runtime/task registry, and AROT audit.
- The branch contains a dedicated XParallel test workflow and a separate main-branch Render deployment workflow. The latter is scoped to pushes on `main`; this programme must not merge or trigger production deployment.

## API and trust-boundary map

| Surface | Current owner | Observed contract | Finding |
|---|---|---|---|
| Next.js `app/api/chat/route.js` | Next.js server route | Proxies to XParallel `/chat` using server-side `XP_TOKEN`; pins actor/workspace to `elle-preview` / `preview`; disables memory | Safe preview posture; not authenticated multi-user chat |
| Python `api/index.py` | Vercel Python entrypoint | Also proxies to XParallel `/chat` using server-side `XP_TOKEN` | Was accepting browser-supplied workspace/actor and memory flag; patched in this branch to the same isolated preview context |
| XParallel `POST /chat` | `xparallel/server.py` | Requires machine `XP_TOKEN`; reads workspace/actor and `use_memory` from JSON | Machine authentication is not human identity. Must only receive trusted tenant context from a server-side adapter |
| ƎllE / Omni / Parallel / XParallel selected APIs | `xparallel/enterprise_auth.py` + `tenant_identity.py` | Verify signed `X-Enterprise-Identity` claims and authorize action | Good foundation; upstream NexAI authorization-code protocol now exists, but enterprise callback/session handoff remains missing |
| Public XParallel APIs | `xparallel/server.py` | Origin/rate-limit controlled public intent/build/route/health endpoints | CORS/origin is not authorization; keep public operations non-sensitive and non-executing |

### Security correction made in this review

The legacy Python chat proxy in `api/index.py` previously forwarded browser-controlled `workspace_id`, `actor`, and `use_memory` fields. A caller could therefore ask the machine-authenticated backend to read a workspace partition selected in JSON if that proxy were exposed.

It now pins:
- `workspace_id = preview`
- `actor = elle-preview`
- `use_memory = false`

The source-level safety test `test_legacy_python_chat_proxy_cannot_trust_browser_tenant_or_memory_flags` was added to `tests/test_oneai_interface.py`. This patch deliberately does not enable authenticated multi-user chat; it removes an unsafe preview path until the identity handoff is complete.

## Persistence inventory and duplication boundaries

| Store | Config / default | Responsibility | Reconciliation decision |
|---|---|---|---|
| Memory Vault | `XP_MEMORY_DB`; serverless default `/tmp/xparallel_memory.sqlite3`, otherwise `xparallel_memory.sqlite3` | Keyword-searchable memory source text, summaries and tags | Canonical low-level XParallel memory store for current chat retrieval |
| Conversation Store | `XP_MEMORY_DB`; same default path as Memory Vault | Workspace-partitioned chat transcripts | Co-located tables are intentional; preserve shared DB setting and avoid a second transcript DB |
| Omni Knowledge Genome | `OMNI_DB`; default `oneai_omni.sqlite3` | Knowledge records, sources, versions, verifications and events | Separate domain store today; evaluate whether to retain separate DB or migrate only after schema/consumer inventory |
| Roaming Registry | `XP_ROAMING_DB`; default `xparallel_roaming.sqlite3` | Runtime registry, hashed runtime credentials and queued tasks | Separate operational store; do not mix with personal memory |
| NexAI identity/workspace/conversation/memory | NexAI `database_url`; default SQLite `nexai.db` | Independent NexAI account, workspace, session-backed user identity and app data | Must remain NexAI-owned; no direct DB/session sharing with AI Enterprise |

Important limitation: current serverless defaults may use ephemeral `/tmp` storage. A passing local SQLite test does not prove persistence across serverless cold starts or deployments. Any persistent hosted database or volume must be zero-cost and explicitly verified before claiming durable production memory.

## Runtime and provider boundary

- The Next.js route calls the XParallel server-side `/chat` endpoint; the browser does not receive `XP_TOKEN`.
- XParallel `/chat` uses the hybrid adapter, which attempts configured local Ollama first and permits a free-cloud fallback only with explicit operator configuration and an availability flag.
- Ollama is not bundled with this repository and must be reachable from the backend host. A mobile browser or the user's phone is not evidence of a model runtime.
- The legacy paid-provider chat service remains in the repository. The default `/chat` path should not call it; keep it disabled unless a separate explicit approval changes the zero-cost policy.
- Provider catalog entries and UI labels are not evidence of provider connectivity.

## Test and workflow inventory

The branch includes focused tests for tenant identity, enterprise authorization, hybrid chat, memory retrieval, conversation storage, Omni Genome, roaming tasks/workers, provider catalog, and interface safety. The XParallel workflow runs compile checks, JS syntax checks and these focused Python test suites.

The workflow does not constitute completed browser SSO, live-host Ollama, serverless persistence, backup/restore or full 113-component verification.

## Next M0 inspection queue

1. Complete the API route inventory from the full `xparallel/server.py` dispatch table and verify every user-data route has a deliberate authentication class.
2. Inspect all SQLite schema owners and all environment-variable defaults; document which tables share files and which are separate.
3. Inspect `elle_lifecycle.py`, `audit_repository.py`, `arot_evidence.py`, `roaming_registry.py`, and `parallel_intelligence.py` for workspace predicates, state transitions, retention and replay behavior.
4. Compare the base branch and PR #61 file-by-file; identify unmerged feature work that must be preserved.
5. Inspect the independent IDEAS repository and NexAI PR #1 without merging either into AI.

## M1 implementation gate

Do not use the legacy `/identity` assertion endpoint as browser SSO. NexAI PR #1 now also implements a separate authorization-code + PKCE S256 server protocol; the enterprise callback, server-to-server exchange client and AI-owned session handoff remain to be connected.

The next implementation must introduce:
- allow-listed redirect URIs and a stable client identifier;
- cryptographically random `state` and PKCE S256 challenge validation;
- explicit user consent;
- one-time authorization codes stored hashed, with short expiry and atomic consumption;
- server-to-server token exchange authenticated by a confidential client credential;
- proof of PKCE verifier and exact redirect URI at exchange;
- AI-owned session creation after signature, issuer, audience, expiry and membership claims are verified;
- replay, expiry, wrong-client, wrong-redirect and cross-workspace denial tests.

Until a canonical application origin is confirmed, use only local test callback URLs. Do not guess or add production redirect URIs, configure shared secrets, or alter Squarespace DNS.

## Current status

- Initial M0 high-risk topology review: completed for the paths listed above.
- M0 full repository and route inventory: still in progress.
- Legacy Python proxy preview isolation: patched; XParallel Integration Tests run #160 passed.
- M1 NexAI authorization-code + PKCE server protocol: implemented on the independent NexAI development branch; browser consent UI and AI Enterprise callback/session integration remain outstanding.
- No merge, deployment, paid resource activation, shared-secret provisioning or production configuration change was performed.


## XParallel server route inventory — first pass

The dispatch review of `xparallel/server.py` found the following route families. This is a route-level inventory, not a substitute for testing every handler's behavior.

| Route family | Intended access class | Current observation / next check |
|---|---|---|
| `/health` | Liveness | Public health response; avoid returning secrets |
| `/public/health`, `/public/system`, `/public/xparallel/access` | Public read-only | Origin-checked; CORS is not authorization |
| `/public/ask`, `/public/build`, `/public/route`, `/public/solution`, `/public/verify`, `/public/graph/search` | Public, rate-limited | Keep non-sensitive; verify no unintended execution or private memory exposure |
| `/api/elle/tasks*` | Human identity + action role | Signed enterprise identity is required |
| `/api/omni/records*`, `/api/omni/search` | Human identity + action role | Signed enterprise identity is required; workspace scoping in store also applies |
| `/api/parallel/research`, `/api/xparallel/dispatch` | Human identity + action role | Signed enterprise identity is required; dispatch remains approval-gated |
| `/roaming/register`, `/roaming/tasks/dispatch`, `/roaming/discover` | Machine/service credential | Verify per-runtime capability, tenant and task policy |
| `/roaming/heartbeat`, `/roaming/tasks/claim`, `/roaming/tasks/complete` | Runtime-specific credential | Verify lease expiry, ownership, replay and idempotency |
| `/provider/route` | Machine/service credential | Verify provider allow-list and secrets remain server-side |
| `/conversations*`, `/memory/*`, `/chat`, `/world/plan`, `/repair/jobs` | Machine/service credential currently | Not yet an authenticated multi-user human API. Do not expose browser access with client-controlled workspace claims |
| `/execute`, `/experiment` | Machine credential + separate execution approval for execution | Keep sandbox and approval checks mandatory |
| `/registry`, `/services`, `/knowledge/*`, `/fetch`, `/graph*`, `/billing/preview`, `/agent/plan`, `/route`, `/build` | Mixed legacy/private/public contract | Complete per-handler authorization and data classification audit before external exposure |

### Additional security note

The current `/chat` endpoint authenticates the calling service using `XP_TOKEN`, then uses workspace and actor values in its request JSON to choose memory scope. That is acceptable only behind a trusted server proxy that pins preview context or derives tenant context from a verified user session. The patched Next.js and Python preview proxies now pin the non-personal preview workspace and disable memory. The future authenticated route must attach signed tenant identity or derive context server-side; never accept these fields as proof of user membership.
