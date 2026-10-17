# OneAI AI Mixer configuration

The authenticated `POST /chat` endpoint uses the shared provider-neutral Mixer. The Mixer does not guess model IDs or claim providers are available unless their model and key are configured.

## Required configuration

Set `XP_MIXER_MODELS_JSON` as a server-side environment variable containing up to four entries, one per provider family. Use model IDs currently enabled for your own provider account.

```json
[
  {"provider":"openai","model_id":"YOUR_ENABLED_OPENAI_MODEL"},
  {"provider":"anthropic","model_id":"YOUR_ENABLED_CLAUDE_MODEL"},
  {"provider":"google","model_id":"YOUR_ENABLED_GEMINI_MODEL"},
  {"provider":"moonshot","model_id":"YOUR_ENABLED_KIMI_MODEL"}
]
```

Configure the matching server-side secrets for the providers you want enabled:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `MOONSHOT_API_KEY`

Do not put these secrets in frontend JavaScript, public environment variables, Git commits, or client requests. The supported API endpoints are fixed to the official HTTPS host for each provider; custom endpoint hosts are rejected.

Optional controls:

- `XP_MIXER_TIMEOUT`: overall provider-call budget in seconds (default 25, bounded to 45).
- `XP_MIXER_MAX_OUTPUT_TOKENS`: per-call output limit (default 1200).
- `XP_MIXER_MAX_INPUT_CHARS`: maximum serialized chat input (default 12000).
- `XP_MIXER_SYNTHESIZER`: provider family to prefer for synthesis (openai, anthropic, google, or moonshot).

## Response evidence

The response includes the final answer and a `mixer` object with state, provider/model IDs, call status, latency, provider-reported token counts when returned, SHA-256 response hashes, errors, skipped-provider reasons, and synthesis evidence. Missing token counts remain null; no estimates are substituted.

When exactly one provider succeeds, the answer is returned as `partial` and the response does not claim cross-provider synthesis. If no configured provider returns a usable answer, the endpoint returns `mixer_unavailable` and HTTP 503. A multi-provider synthesis failure falls back to one successful provider answer with an explicit partial state.

## Verification status

Unit tests cover configuration validation, no-provider behavior, telemetry extraction, response hashing, and secret/error redaction. A test result is not considered verified until the repository workflow actually executes and reports it. Real provider calls additionally require valid provider credentials and currently supported model IDs in the hosting environment.
