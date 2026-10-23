# Independent OneAI assistant (local-first)

OneAI now selects an open-source model served by Ollama when `XP_AI_API_KEY` is not set. The default is `qwen2.5:3b` at `http://127.0.0.1:11434/api/chat`. This default does not require a paid AI API key or Python provider SDK.

## Important deployment fact

This code is an adapter, not an Ollama installation. A real answer requires Ollama to be installed and running somewhere reachable and the selected model to be downloaded. Vercel's Python function does not automatically include Ollama or its model files. On a hosted deployment, use a separate Ollama host with HTTPS and set `XP_OLLAMA_URL` and `XP_OLLAMA_MODEL` in that backend's environment. Do not expose an unauthenticated Ollama port directly to the public internet.

## Run locally

1. Install Ollama from https://ollama.com/.
2. Download the default model: `ollama pull qwen2.5:3b`.
3. Ensure Ollama is running and listening on `127.0.0.1:11434`.
4. Start the existing XParallel server. No `XP_AI_API_KEY` is needed for local Ollama.
5. Send a chat request through the existing OneAI chat route. A provider failure is returned honestly; no simulated AI answer is generated.

## Configuration

- `XP_OLLAMA_URL`: defaults to `http://127.0.0.1:11434/api/chat`. HTTP is accepted only for loopback. Remote endpoints must use HTTPS.
- `XP_OLLAMA_MODEL`: defaults to `qwen2.5:3b`; choose a model actually installed on the Ollama host.
- `XP_AI_API_KEY`: optional compatibility path for an existing OpenAI-compatible chat-completions provider. When set, that path takes precedence.
- `XP_AI_CHAT_COMPLETIONS_URL` and `XP_AI_MODEL`: optional provider endpoint/model for that compatibility path.
- `XP_AI_TIMEOUT_SECONDS`: request timeout; defaults to 90 seconds.

SQLite conversation and memory stores remain the default. PostgreSQL remains opt-in. Do not store provider credentials in frontend code or commit secrets. No production deployment is performed by this branch.
