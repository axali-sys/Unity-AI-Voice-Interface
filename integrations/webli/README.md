# Webli → XParallel public client

This is the first code-level integration seam for the Webli-built XParallel Dual Space UI. It uses the existing public API routes in `xparallel/server.py` and does not change or replace backend routes.

## Supported calls

- `health()` → `GET /public/health`
- `manifest()` → `GET /public/xparallel/access`
- `ask(query)` → `POST /public/ask`
- `buildPlan(query)` → `POST /public/build`
- `route(query)` → `POST /public/route`

These endpoints are planning/knowledge APIs. They do **not** claim to launch an Android clone or run a sandbox experiment.

## Connect it in Webli

1. Open the existing Webli project and its code/source editor.
2. Import `createXParallelClient` from this file, or copy the file into the Webli project if it cannot import from GitHub.
3. Set `baseUrl` to the deployed XParallel API base URL using Webli's project configuration. Do not guess the URL; use the actual current deployment URL.
4. Call `health()` on a user-initiated “Connect / Check connection” action and show the returned status and version.
5. Call `buildPlan(query)` for a plan preview. Label the result “Plan” or “Proposed experiment,” not “Executed.”
6. If the request fails, display “Not connected” or the error message. Do not display a green/active sandbox state based on a mock value.

Example:

```js
import { createXParallelClient } from "./xparallel-client.js";

const xparallel = createXParallelClient({
  baseUrl: import.meta.env?.VITE_XPARALLEL_API_BASE_URL
});

const status = await xparallel.health();
const plan = await xparallel.buildPlan("Describe the intended test");
```

If Webli does not support `import.meta.env`, use its documented environment/configuration mechanism. Never hardcode secret values into the client.

## Important deployment requirements

- The backend's `XP_PUBLIC_ORIGINS` must include the actual Webli preview/published origin. The current backend defaults to Axaliai domains, so a Webli origin may be rejected until explicitly configured.
- Keep `XP_TOKEN` and `XP_EXECUTION_APPROVAL_TOKEN` server-side. This browser client intentionally does not support private execution routes.
- `/public/health` confirms API health only. It does not prove Docker sandbox availability, local Android isolation, or end-to-end execution.
- Do not enable deployment controls until a separately authenticated, server-enforced approval flow is implemented and tested.
- This adapter has not yet been run inside Webli because the specific Webli project URL/source has not been provided.
