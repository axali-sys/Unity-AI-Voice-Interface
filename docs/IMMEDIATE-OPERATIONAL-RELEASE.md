# Immediate AI Enterprise Operational Release — Development Track

**Repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Branch:** `enterprise/axaliai-completion`  
**State:** development integration slice; not production-ready  
**Policy:** zero-cost only; no production deployment; no merge to main/master.

## What is present in the existing repository

The branch reuses the existing application and service modules rather than replacing them with a new starter:

- Next.js assistant workspace and server-side chat/provider API proxies.
- XParallel API, service registry, authorization helpers, task queue and roaming-worker foundations.
- SQLite-backed memory vault, conversation store and repair-job store.
- Provider catalog and local-first hybrid chat adapter.
- ƎllE task lifecycle with state transitions, risk levels, human approval and verification evidence.
- Omni knowledge records, source metadata, version history and explicit verification evidence.
- AROT audit/evidence hooks.
- Signed tenant identity primitive and fail-closed route authorization for ƎllE, Omni, Parallel Research and XParallel dispatch.
- The source 113-component register copied into this branch without changing its initial Unverified/Experimental statuses.

## Changes in this release slice

1. Added `xparallel/enterprise_auth.py` to validate the separate `X-Enterprise-Identity` header and enforce role/action permissions.
2. Connected that guard to the enterprise user API routes. Workspace and actor values are derived from signed claims; client-supplied workspace/actor values are ignored.
3. Preserved `XP_TOKEN` as a machine/service credential, not an end-user identity.
4. Changed default chat routing to local Ollama first and explicitly verified free-cloud fallback only. The default chat path no longer invokes the legacy paid-provider chat adapter.
5. Pinned unauthenticated browser preview chat to a non-personal preview workspace and disabled memory retrieval until trusted login and membership are available.
6. Added route authorization and zero-cost behavior tests to the existing integration suite.

## Required local configuration

A local development setup requires Python 3.12+, Node.js/npm, and a machine or server on which the backend can reach Ollama. For a same-machine backend/model:

```bash
ollama serve
ollama pull qwen2.5:3b
```

Backend environment (use unique locally generated secrets; never commit them):

```bash
export XP_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export XP_IDENTITY_SIGNING_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export XP_HUB_LOCAL_URL="http://127.0.0.1:11434"
export XP_HUB_LOCAL_MODEL="qwen2.5:3b"
python -m xparallel.server
```

Frontend in another terminal:

```bash
npm install
export XP_API_URL="http://127.0.0.1:8787"
export XP_TOKEN="<same local XP_TOKEN>"
npm run dev
```

These commands are for local development only. If the backend runs remotely, its `localhost` is not the user's phone or laptop; the model endpoint must be reachable from the backend and protected. Do not expose Ollama directly to the public internet.

## What is not yet operational

- No trusted login provider is wired to issue identity tokens after verifying user membership.
- No browser login/session flow or multi-user membership adapter is connected.
- Therefore the enterprise routes fail closed without a valid signed token. The UI does not yet mint or attach those tokens.
- NexAI and IDEAS have separate repositories and isolated readiness branches; neither is absorbed into this repository. Their runtime adapters still require independent audit and versioned interface contracts.
- Ollama is not provisioned/hosted by this repository. A suitable user-owned or already-available machine is required; no free cloud compute is assumed.
- Provider directory status is configuration metadata, not proof of live availability or free quota.
- Omni retention/deletion/export/backup/restore and concurrency review remain incomplete.
- The full 113-component register remains unverified source-by-source. Existing names are not treated as implemented without code and tests.
- No production deployment or live environment configuration has been changed.

## Verification evidence

- GitHub Actions XParallel Integration Tests run #149 completed successfully: compile, JavaScript syntax, roaming/task queue, provider catalog, hybrid chat, memory, conversation, Omni, tenant identity, enterprise route authorization and ƎllE lifecycle steps all passed.
- A later integration slice adds end-to-end HTTP checks for signed tenant workspace isolation and ensures default chat does not call the legacy paid-provider route. The resulting CI run #153 passed all workflow steps, including both tests.
- Passing CI validates the covered test behavior only. It does not establish production readiness or live provider/host availability.

## Next activation gates

1. Complete trusted login + workspace membership adapter and browser session flow.
2. Add authenticated UI workflows for ƎllE tasks and Omni knowledge history.
3. Prove live local Ollama inference from the actual backend host.
4. Run full HTTP, persistence, tenant-isolation, recovery and security tests.
5. Audit and connect NexAI and IDEAS through explicit independent adapters.
6. Reconcile every C001–C113 and P001–P015 against code/tests/evidence and retain honest statuses.
7. Review the draft PR before any release decision. Main/master and production remain untouched.
