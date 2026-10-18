# XParallel infrastructure verification

This checklist applies to the existing `axali-sys/Unity-AI-Voice-Interface` repository. The Render Blueprint is configuration, not proof that a service is deployed or that secrets exist.

## Hosting and environment

- Render service: `axaliai-mainnet`, start command `python xparallel/server.py`, health path `/health`.
- `render.yaml` declares the provider, roaming, authentication, and database-path environment variable names. Values marked `sync: false` must be configured securely in the Render dashboard; they are deliberately not stored in Git.
- The Bolt frontend origin `https://xparallel-ai-infrast-q4lg.bolt.host` is included in the public-origin allowlist. The deployed backend must also have this exact value in `XP_PUBLIC_ORIGINS` for browser requests to pass origin checks.
- No persistent disk is created by this change. Before production, mount durable storage and set both `XP_MEMORY_DB` and `XP_DB_PATH` to writable paths on that disk. Without durable storage, SQLite data may be lost on redeploy/restart.
- Configure `XP_MIXER_MODELS_JSON` with actual enabled model IDs and only the corresponding provider API keys. Configure `TAVILY_API_KEY` for live roaming search. Worker URLs/tokens require an exact host allowlist and network egress controls.

## Run safe checks

Use the actual API backend URL, not the Bolt frontend URL unless the API is served from the same origin:

```bash
XP_BASE_URL=https://YOUR-API-HOST.example python -m xparallel.infra_verify
```

The default run checks `/health`, `/public/health`, `/public/system`, `/public/xparallel/access`, and verifies that unauthenticated access to `/memory` returns 401. It does not make paid provider calls or write data.

Set the configured frontend origin and bearer token for authenticated checks:

```bash
XP_BASE_URL=https://YOUR-API-HOST.example \
XP_PUBLIC_ORIGIN=https://xparallel-ai-infrast-q4lg.bolt.host \
XP_TOKEN=YOUR_SERVER_TOKEN \
python -m xparallel.infra_verify
```

The approval-gate probe sends a minimal file payload without the approval header and expects `403 human_approval_required`; it must not execute the payload.

Opt-in tests:

- `--write-memory`: creates a temporary memory record, searches for it, and deletes it.
- `--live-ai`: calls the configured AI Mixer and may incur provider costs.
- `--live-roam`: calls configured roaming search and may incur provider costs.

For example, use `--live-ai --live-roam` only after credentials, model IDs, origin configuration, and rate limits have been checked. A successful HTTP health response is liveness only. A `/public/system` response is configuration metadata only. Live provider/roaming calls, memory persistence across restart, Docker sandbox execution, voice, and per-user workspace isolation require their own evidence.

## Current verification limitation

The Vercel project metadata is accessible, but deployment details and environment-variable inventory returned 403 for the connected account scope during this verification. The latest Vercel deployment was reported as queued; live provider calls and the Bolt-hosted URL could not be independently reached from the current execution environment. Do not mark production ready until those access blockers are resolved and the checks above are run against the actual backend.
