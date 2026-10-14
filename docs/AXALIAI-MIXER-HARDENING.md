# Axaliai Universal AI Mixer — Hardening and Runtime Configuration

This document records the hardening follow-up after PR #30. It is not a claim that live provider credentials or production deployment have been verified.

## Provider defaults

The default provider IDs are based on the official model catalogs as checked on 2026-10-14:

- Anthropic: `claude-sonnet-4-6` — https://docs.anthropic.com/en/docs/about-claude/model-deprecations
- OpenAI: `gpt-6.1-sol` using Chat Completions — https://developers.openai.com/api/docs/models
- Google: `gemini-3.8-flash` — https://ai.google.dev/gemini-api/docs/models

These are documentation checks, not live API smoke tests. Provider account access, billing, regional availability, and current API behavior still require runtime verification. Moonshot is not included in the default registry because the current model ID and endpoint were not confirmed from an official Moonshot source during this pass. It can be configured through `XP_MIXER_MODELS_JSON` after verification.

## Authentication and workspace isolation

The legacy `XP_TOKEN` remains a **single-tenant administrative credential**. Set `XP_DEFAULT_WORKSPACE_ID` to the workspace for that deployment. Request JSON cannot override the workspace used by private mixer memory retrieval or approval tickets.

For multi-workspace deployments, configure per-workspace bearer credentials in the server environment variable `XP_WORKSPACE_TOKENS_JSON`. Example shape (replace all placeholders with unique, high-entropy secrets; do not commit actual secrets):

```json
{
  "workspace-alpha": {"token": "<secret-alpha>", "role": "owner"},
  "workspace-beta": {"token": "<secret-beta>", "role": "operator"}
}
```

The client sends `Authorization: Bearer <workspace-token>`. Roles are limited to `owner`, `admin`, `operator`, and `viewer`. Each configured workspace token is mapped to its workspace server-side; a caller-supplied `workspace_id` is ignored for the private mixer/approval path. Use a secret manager for these values.

## Action-bound sandbox approval

Approval-required plugin calls use two steps:

1. An authorized operator sends `POST /plugins/approve` with the plugin ID, action, and exact payload, plus the normal bearer token and the separate `X-XParallel-Approval` credential.
2. The server returns a random ticket that expires after 120 seconds. Send that ticket with `POST /plugins/execute` and the exact same plugin/action/payload.

The ticket is bound to workspace, authenticated principal, action, and a canonical payload hash. It is single-use; expired, replayed, or mismatched tickets are rejected. This is still a server-configured approval credential, not a full interactive approval UI or cryptographic signature from a named human identity. Keep the approval credential private.

## AI Memory storage

AI Memory now uses a workspace-scoped SQLite database configured by `XP_AI_MEMORY_DB`; it no longer treats a shared JSONL file as the memory store. Records have IDs, workspace ownership, metadata, creation/expiry timestamps, and soft-deletion timestamps. `XP_AI_MEMORY_RETENTION_DAYS` defaults to 365; each stored record can specify 1–3650 retention days. Search excludes expired, deleted, and other-workspace records. Delete is scoped to the authenticated workspace.

**Persistent volume required:** SQLite only persists across restarts if `XP_AI_MEMORY_DB` points to durable storage mounted by the hosting platform. Do not place the database on ephemeral serverless storage and assume it is durable. Back it up and test restore. This adapter provides bounded keyword retrieval, not embeddings/vector search; semantic retrieval can be added behind the same workspace-aware interface.

## Live verification boundaries

Unit tests use mocked external HTTP calls where appropriate. Live tests for Brave, GitHub, Drive, and AI model providers require authorized credentials. Google Drive currently uses an access token supplied as `GOOGLE_DRIVE_ACCESS_TOKEN`; token refresh/OAuth consent is not implemented in this adapter and must be provided by the deployment's credential broker. Do not mark Drive production-ready until expiry/refresh and scopes are verified.

No production merge or deployment is authorized by this document.
