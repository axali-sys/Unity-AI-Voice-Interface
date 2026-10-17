# OneAI Core Roaming Engine

OneAI roaming is a core provider-neutral capability. The public API endpoint is
`POST /public/roam` with JSON `{"query":"..." }`. It performs real provider calls
only when configured and returns `status: "roaming_unavailable"` with setup
instructions when no live route succeeds.

## Live web search

Set `TAVILY_API_KEY` as a server-side environment secret. The engine sends the
query to Tavily and returns its answer, HTTPS source URLs, snippets, provider
status, and latency. Do not place secrets in frontend code or commit them.

## Independent remote workers

Optionally set `ONEAI_ROAMING_WORKERS` to a JSON array of trusted worker services:

```json
[
  {
    "name": "worker-eu",
    "url": "https://worker.example.net",
    "token": "INJECT_FROM_SECRET_MANAGER"
  }
]
```

Each worker must implement `POST /v1/roam`, accept a Bearer token, and return
JSON with optional `answer` and `sources` fields. The URL must use HTTPS. The
engine treats workers as independent services; it does not assume a single
server can satisfy every task. Worker deployment, credentials, health, and
capacity remain operator responsibilities.

## Safety and truthful status

- A plan is not live browsing; unavailable providers are listed in
  `skipped_providers`.
- Search results do not imply login to arbitrary accounts or permission to act.
- Consequential external actions still require authorized connectors and
  explicit approval.
- Only configure worker endpoints that you control or explicitly trust.
- Configure provider secrets in the hosting platform, never in source control.

## Validation

Run `python -m unittest tests.test_roaming_engine` from the repository root.
Live provider checks require a valid configured API key and network access.
