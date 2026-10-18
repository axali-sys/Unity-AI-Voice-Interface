# OneAI developer quick start

This guide applies to the existing Unity-AI-Voice-Interface repository. It does not imply that a production deployment is currently available.

## Runtime

- Python 3.10 or newer
- Standard-library HTTP API; provider calls use Python's standard library
- Optional Docker runtime for bounded XParallel experiments
- A durable writable path for SQLite conversation and memory storage in deployments

Start the API from the repository root:

```bash
python xparallel/server.py
```

The server listens on the port supplied by the host environment or XP_PORT (default 8787). Configure XP_TOKEN and XP_EXECUTION_APPROVAL_TOKEN as server-side secrets before enabling authenticated API operations.

## Provider configuration

Set XP_MIXER_MODELS_JSON and only the provider keys you want to enable. Model IDs must be currently enabled in the respective provider account; do not copy sample placeholder IDs into production.

```json
[
  {"provider":"openai","model_id":"YOUR_ENABLED_OPENAI_MODEL"},
  {"provider":"anthropic","model_id":"YOUR_ENABLED_CLAUDE_MODEL"},
  {"provider":"google","model_id":"YOUR_ENABLED_GEMINI_MODEL"},
  {"provider":"moonshot","model_id":"YOUR_ENABLED_KIMI_MODEL"}
]
```

Provider secrets:

- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GOOGLE_API_KEY
- MOONSHOT_API_KEY

See ONEAI_AI_MIXER.md for evidence fields and timeout controls.

## Roaming configuration

Set TAVILY_API_KEY for live web search. Trusted workers are optional and must be configured with both ONEAI_ROAMING_WORKERS and ONEAI_ROAMING_ALLOWED_HOSTS. See ONEAI_ROAMING.md for the exact worker protocol and security limits.

## API surface

| Route | Access | Purpose |
|---|---|---|
| GET /health | Public host health | Runtime liveness |
| GET /public/health | Allowed frontend origin | Liveness and sandbox availability |
| GET /public/system | Allowed frontend origin | System configuration manifest; not proof of live provider health |
| GET /public/xparallel/access | Allowed frontend origin | Gateway access contract |
| POST /chat | Bearer token | Shared AI Mixer chat with optional memory retrieval |
| POST /public/ask | Allowed frontend origin, rate-limited | Existing knowledge retrieval |
| POST /public/build | Allowed frontend origin, rate-limited | Existing XParallel plan generation |
| POST /public/route | Allowed frontend origin, rate-limited | Existing intent routing |
| POST /public/roam | Bearer token plus allowed origin and rate limit | Live search through configured providers; retrieval only |
| POST /world/plan | Bearer token | XParallel planning |
| POST /experiment | Bearer token | Bounded sandbox experiment, subject to runner availability |
| POST /execute | Bearer token and explicit approval | Consequential execution path; do not expose directly to an unauthenticated browser |

Public-origin restrictions and bearer authentication are different controls. CORS does not authenticate a caller.

## Durable storage and identity

Set XP_MEMORY_DB to a durable, writable database path or mount. Back it up according to the hosting provider's recovery process. Do not treat a client-supplied workspace_id as a verified user identity. Before multi-user production, bind authenticated principals to server-enforced workspace IDs and test cross-user access attempts.

## Deployment

Keep the existing Render/Vercel architecture until each host's current configuration and access can be verified. Do not deploy the candidate PR solely because it builds. Configure exact XP_PUBLIC_ORIGINS, server-side provider secrets, durable storage, sandbox support, and outbound network controls; then run the acceptance gates in ONEAI_RELEASE_READINESS.md.

## Test commands

```bash
python -m compileall -q xparallel tests
python -m unittest discover -s tests -v
```

The focused candidate tests are also included in the existing XParallel integration workflow. A test is verified only after the command is executed and its output inspected. Mocked tests do not count as live provider or deployment verification.
