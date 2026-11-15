# Oneaiplus Conversation Persistence — Implementation Contract

Date: 2026-11-15
Canonical Lovable project: c2232890-a16d-4289-b2f8-c8de6365a7b4
Source inspected: 3fac96efc001f394622301568f2f42417c08a87a
Status: implementation contract only; no application or database changes made.

## 1. Current verified behavior
- `src/components/HomeChat.tsx` uses AI SDK `useChat` with `DefaultChatTransport` at `/api/chat` and obtains the current Supabase access token for each request.
- Messages exist only in the component's in-memory chat state. The UI explicitly says the chat is not saved and clears when leaving the page.
- `src/server/chat.server.ts` independently authenticates the bearer token, checks `is_oneai_owner()`, then sends the request to the Lovable AI Gateway.
- Existing canonical storage consists of `projects`, `memories`, and `audit_events`. The current migrations define owner-only RLS through `user_id = auth.uid()` and `is_oneai_owner()`.
- `src/lib/diagnostics.functions.ts` exposes owner-protected memory list/create/delete operations. Memory creation/deletion attempts to append audit events, but the audit insert result is not checked; a failed audit write can therefore go unnoticed.
- There is no existing conversation/message persistence table or conversation API in the inspected source.

## 2. Data model to add (proposal; do not apply until isolated database is confirmed)

### `conversations`
- `id uuid primary key default gen_random_uuid()`
- `user_id uuid not null references auth.users(id) on delete cascade`
- `title text not null default 'New conversation'` with a 1–160 character check
- `status text not null default 'active'` restricted to `active` or `archived`
- `created_at timestamptz not null default now()`
- `updated_at timestamptz not null default now()`
- `last_message_at timestamptz`

### `conversation_messages`
- `id uuid primary key default gen_random_uuid()`
- `conversation_id uuid not null references public.conversations(id) on delete cascade`
- `user_id uuid not null references auth.users(id) on delete cascade`
- `client_message_id text not null` (stable UI message ID, length limited)
- `role text not null` restricted to `user` or `assistant` for the first release
- `content text not null` with an explicit maximum length
- `created_at timestamptz not null default now()`
- Unique constraint `(conversation_id, client_message_id)` to make retries idempotent.
- Index `(conversation_id, created_at, id)` for ordered transcript reads and `(user_id, updated_at desc)` for conversation listing.

Store text-only messages in v1. Do not persist tool calls, arbitrary JSON parts, hidden reasoning, provider secrets, raw request headers or access tokens. If attachments or tool results are introduced later, use separately typed records and explicit authorization.

## 3. Database security contract
- Enable RLS on both tables.
- Policies must require `user_id = auth.uid()` AND `public.is_oneai_owner()` for every SELECT/INSERT/UPDATE/DELETE path.
- For `conversation_messages`, policies must also verify that the referenced parent conversation belongs to the same authenticated owner. Do not rely solely on a client-supplied `user_id` or conversation ID.
- Revoke table privileges from `PUBLIC` and `anon`; grant only the minimum required operations to `authenticated` and service role as needed by the server architecture.
- Keep `is_oneai_owner()` as the canonical admission check; do not copy the donor workspace RLS policies.
- Add database constraints for valid roles, bounded title/content lengths, and consistent user ownership between parent and child rows.
- Avoid SECURITY DEFINER functions unless necessary. Any such function must use an empty or tightly controlled search_path, explicit grants/revokes, and tests for privilege escalation.

## 4. Server API contract
All operations must use the existing `requireOwner` middleware or the same independently verified bearer-token plus `is_oneai_owner()` check used by `/api/chat`.

1. `listConversations`: return only the current owner's active/archived conversation metadata; paginate with a bounded page size and stable cursor.
2. `createConversation`: server assigns `user_id` from verified context; ignore/reject caller-supplied owner IDs.
3. `getConversation`: require owner-scoped parent lookup before loading messages; bounded page size, chronological order.
4. `appendMessage`: validate conversation ownership; accept only user/assistant text messages; enforce byte, character, count and role limits; use idempotency key; user message is persisted before provider invocation.
5. `completeAssistantMessage`: persist only the final assistant text after a successful provider response; do not save partial/error placeholders as successful assistant turns.
6. `renameConversation`: owner-scoped update, bounded title.
7. `archiveConversation`: owner-scoped status update.
8. `deleteConversation`: explicit user action, owner-scoped delete with cascade; record a minimal audit event without copying message contents into the audit log.

## 5. Streaming and failure semantics
- Persist the user message before starting the model stream. If persistence fails, do not call the provider.
- Stream the assistant response to the client as today, while buffering only within a strict output limit.
- Persist the final assistant message only when the provider stream completes successfully.
- If the stream fails or is cancelled, retain the user message and return a clear error. Do not store a fabricated assistant answer.
- If final persistence fails after the provider answered, surface that the answer was delivered but not saved; do not silently claim persistence succeeded.
- A retry must not duplicate the user message. Use the stable `client_message_id` uniqueness key.
- Never place XParallel execution, tool invocation or autonomous side effects inside this conversation persistence path. Ordinary chat and XParallel authorization remain separate.

## 6. UI behavior
- Add a conversation list with New, Open, Rename, Archive and Delete actions.
- Show explicit save state: Saving, Saved, or Not saved / retry. Do not show a Saved state before the database confirms the write.
- Keep the current chat route and AI SDK transport. Add conversation ID as validated request context, not as an authority claim.
- Do not automatically turn saved conversations into model memory. Jellybox memory extraction must remain a separate, reviewable user-controlled workflow.
- Keep the UI honest when the AI provider is unavailable or out of credits; saved transcripts remain readable without a working model connection.

## 7. Required tests before enabling
- Owner can create/list/read/append/rename/archive/delete their own conversations.
- Unauthenticated and non-owner callers are rejected on every API operation.
- A forged `user_id`, another owner's conversation ID, and a child message attached to another owner's parent are rejected.
- Anonymous/public roles cannot read or mutate either table.
- Duplicate client message IDs do not create duplicate rows.
- Oversized title, message, request body, message count and page size are rejected.
- Invalid roles, unsupported parts and malformed JSON are rejected.
- Provider 402, 429, 5xx, timeout and cancellation preserve correct transcript state.
- Failed database writes do not call the provider or falsely display Saved.
- Failed audit writes are surfaced or retried according to a documented policy.
- Deletion cascades only within the same owner's conversation and leaves no orphaned messages.

## 8. Audit-write gap to address
`src/lib/diagnostics.functions.ts` currently awaits `audit_events` inserts after memory mutations but does not inspect the returned `{ error }`. This can make an action appear successful even when its audit record failed. The implementation should define whether audit logging is mandatory (mutation rolls back/fails if audit cannot be written) or best-effort (explicitly surfaced and monitored). For security-sensitive actions, prefer transactional mutation-plus-audit through a carefully hardened database function.

## 9. Release gates and isolation
- Do not create or apply migrations until Lovable draft isolation includes an independent database. Current draft metadata reports `backend_kind=local_supabase`; no proof of a separate database was returned.
- Do not send build instructions through the live project message API when they cannot be explicitly scoped to the draft.
- Do not accept the draft into the published project until its diff, database target, migration plan and tests are reviewed.
- No production deployment, publish, merge to `main`, donor deletion or paid service is authorized by this design.

## 10. Acceptance definition
Conversation persistence is complete only when the schema is applied to a confirmed isolated database, RLS negative tests pass, server APIs pass owner/abuse tests, UI confirms saves from database acknowledgements, and the preview is verified end-to-end. A design document or local mock does not meet this definition.