# OneAI roaming configuration

OneAI's `POST /public/roam` endpoint performs authenticated, retrieval-only search. It does not execute instructions against external accounts, devices, or production environments. The route uses the existing public-origin checks and rate limiter, and additionally requires the API bearer token because it can incur third-party service costs.

## Live web search

Set `TAVILY_API_KEY` as a server-side secret. Without it, the endpoint returns `roaming_unavailable` with an explicit setup list rather than pretending that web search occurred.

## Trusted independent workers

Optional workers are operator-managed HTTPS services. Set `ONEAI_ROAMING_WORKERS` to a JSON array of objects:

```json
[
  {"name":"research-worker-1","url":"https://worker.example","token":"SERVER_SIDE_WORKER_TOKEN"}
]
```

Set `ONEAI_ROAMING_ALLOWED_HOSTS` to a comma-separated exact hostname allowlist, for example `worker.example`. The engine rejects non-HTTPS endpoints, URLs with embedded credentials, unlisted hosts, hosts that do not resolve exclusively to globally routable addresses, and HTTP redirects. The allowlist and worker credentials must be configured by the service operator, never by an untrusted request.

Worker contract: `POST /v1/roam` with a bearer token and JSON `{"operation":"search","query":"...","scope":"internet_wide"}`. Return JSON with `operation: "search"` and optional `answer` and `sources` fields. Workers must implement retrieval only; they must not treat this endpoint as permission to perform external actions.

## Status and evidence

`GET /public/system` reports configuration status only. A worker shown as `configured_unprobed` has not been health-checked. A successful `POST /public/roam` response reports the providers actually called, their latency, skipped reasons, and returned HTTPS sources. `execution_performed` remains false because retrieval is not external task execution.

## Security boundaries and remaining production work

The engine applies response-size and timeout limits, rejects redirects, and uses a hostname allowlist plus public-address resolution checks. For higher-assurance production deployments, enforce outbound egress restrictions at the hosting/network layer and pin worker service identities at the gateway. DNS checks alone cannot eliminate every DNS-rebinding race. Worker health probes, persistent registry, circuit breakers, retries, and distributed task state are not yet implemented by this lightweight registry.
