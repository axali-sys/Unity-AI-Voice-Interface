# Axaliai unified interface: Axaliai + UnityAI + XParallel

This branch brings the Axaliai chat interface together with UnityAI-style browser voice input/output and existing XParallel planning, knowledge, and AI Memory routes.

## Added/changed
- `public/axaliai.html`: responsive unified workspace, chat history, browser speech recognition/synthesis, text attachments, memory search, XParallel plan mode, knowledge mode.
- `xparallel/chat_service.py`: authenticated provider-backed chat using existing server-side `XP_AI_API_KEY`, `XP_AI_MODEL`, and optional `XP_AI_CHAT_COMPLETIONS_URL`.
- `xparallel/server.py`: adds authenticated `POST /chat`, uses workspace-scoped memory retrieval and audit logging.

## Server configuration
Set `XP_TOKEN`, `XP_AI_API_KEY`, and `XP_AI_MODEL` in the hosting environment. Optionally set `XP_AI_CHAT_COMPLETIONS_URL` to an HTTPS-compatible endpoint. Never put provider keys in HTML or Git.

## How to serve
The static page is at `/public/axaliai.html` in the repository. Configure the existing static hosting or route to expose it at `/axaliai.html`. The browser connects to the existing XParallel API base URL and requires the API CORS allowlist to include the frontend origin.

## Safety and boundaries
- Chat and memory routes require the XParallel bearer token.
- XParallel plan mode calls `/world/plan` and labels the result as a plan, not an executed job.
- This interface does not bypass the existing execution approval gate on `/execute`.
- Voice is browser speech recognition and synthesis; it does not yet include a server-side voice identity or biometric authentication system.
- Browser chat history is local to that browser; cross-device persistence is not claimed.
- Test the API routes and full existing workflow suite before deployment. This branch is not a production-readiness certification.
