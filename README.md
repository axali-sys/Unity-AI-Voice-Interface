# Axaliai Assistant starter

This repo now includes a polished AI assistant UI that is designed to sit on top of the XParallel backend.

## Run locally

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the dev server:
   ```bash
   npm run dev
   ```

3. Open the app:
   ```bash
   http://localhost:3000
   ```

## Connect to the live backend

Set these environment variables before running the app:

```bash
export XP_API_URL=http://localhost:8787
export XP_TOKEN=your-xparallel-token
```

The UI calls `/api/chat`, which proxies to the backend. The proxy never returns a demo answer. Until trusted user login and workspace membership are connected, preview chat is pinned to a non-personal `preview` workspace and memory retrieval is disabled to prevent cross-user memory exposure.

## Frontend stack

- Next.js
- React
- Tailwind-style custom CSS
- XParallel-compatible API proxy

## Notes

This is a starter Lovable-style assistant interface. It is intentionally clean and launch-ready visually, while keeping the underlying XParallel logic in the existing repo.


## Zero-cost local-first chat (development)

The default backend `/chat` route uses the hybrid adapter: local Ollama first, then only an explicitly enabled and operator-verified free provider. It does not call the legacy paid-provider chat gateway by default.

For a backend running on the same machine as Ollama:

```bash
export XP_HUB_LOCAL_URL=http://127.0.0.1:11434
export XP_HUB_LOCAL_MODEL=qwen2.5:3b
```

Start Ollama and download the model on that machine before starting XParallel. If the backend runs on a different host, `localhost` refers to that backend host; configure a secure HTTPS endpoint only if the remote Ollama gateway is protected. Do not expose Ollama's port publicly.

The chat route returns a clear provider-unavailable response when no local model is configured. A free-cloud fallback is disabled unless its URL/model/key are configured, its free availability is explicitly verified, and `XP_HUB_ALLOW_FREE_FALLBACK=true` is set. Paid providers are not selected by this default path.

## Enterprise identity gate

The ƎllE/Omni/Parallel/XParallel user APIs accept a signed `X-Enterprise-Identity` token, distinct from `XP_TOKEN`. Actor and workspace are taken from signed claims, not request JSON or query strings. The server-side token issuer must only be called after a trusted login provider authenticates the user and a membership service confirms workspace membership. That login/membership adapter and the browser session flow are not yet complete; these APIs intentionally fail closed until then.

This is a development integration slice, not a production release. No default-branch merge, production deployment, paid resource activation, or purchase is part of this branch.
