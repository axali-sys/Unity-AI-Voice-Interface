# Oneaiplus Canonical Source and Chat Runtime Audit

Date: 2026-11-15

## Scope

Read-only inspection of the canonical Lovable project `c2232890-a16d-4289-b2f8-c8de6365a7b4`, including its project metadata, file tree, package manifest, `AGENTS.md`, application shell, home chat component, chat server, owner middleware, project persistence functions, and GitHub server functions.

No application source, database schema, data, deployment, publication, or branch protection settings were changed.

## Canonical project identity and source status

- Lovable project name: `Oneaiplus`.
- Project status: `ready`; latest source commit at inspection: `3fac96efc001f394622301568f2f42417c08a87a`.
- Existing project metadata reports `is_published=true`; this audit did not alter publication.
- `.lovable/project.json` contains only template/revision metadata and does not expose a GitHub repository or branch.
- `AGENTS.md` explicitly says the project is connected to Lovable and that commits pushed to the connected branch sync back to the editor. This is evidence of a connected source-control workflow, but the exact repository and branch are not exposed by the inspected metadata.
- The inspected project also contains server-side GitHub connector functions. Their existence does not prove that the Lovable project's own source-control remote is the same repository.
- The separate XParallel repository `axali-sys/Unity-AI-Voice-Interface` is confirmed accessible through the connected GitHub account, but it must not be assumed to be the canonical Lovable project's own remote.

## Verified runtime findings

### Application identity

- `src/components/AppShell.tsx` renders "OneAI Home" and a "OneAI" brand label.
- `src/components/HomeChat.tsx` uses OneAI wording in its prompt and chat disclaimer.
- `src/server/chat.server.ts` describes the assistant as operating inside the OneAI workspace.
- The project itself is named Oneaiplus. A future identity cleanup should update user-facing labels consistently while retaining distinct names for independent products and modules.

### Chat route and authorization

- The frontend uses AI SDK `DefaultChatTransport` with API path `/api/chat`.
- It obtains the current Supabase access token and sends it as a Bearer token.
- The server independently validates the token with Supabase `auth.getUser`, then calls `is_oneai_owner`; missing auth returns 401 and failed owner authorization returns 403.
- The server validates that messages are an array with 1–100 entries.
- The model call is routed through Lovable AI Gateway using `openai/gpt-6-astra` and a server-side `LOVABLE_API_KEY`.
- Error handling explicitly maps insufficient credits (402) to an out-of-credits response. Prior runtime inspection recorded a 402 credit limitation; therefore model availability must not be inferred from the configured model string.
- Chat messages are held in the component's local `useChat` state. The UI explicitly says the chat is not saved and clears when leaving the page. No conversation persistence was found in the inspected route/component.

### Existing persistence and audit foundation

- `projects.functions.ts` provides owner-protected list/create/update/delete for the existing `projects` table.
- Writes set `user_id` from the authenticated server context rather than trusting a client-supplied owner ID.
- The current project persistence model is narrower than the donor's generic section-scoped workspace record model.
- Any future workspace records or chat history should be designed against the existing RLS and canonical tables first; do not copy donor migrations wholesale or bypass owner middleware.
- Existing project mutations do not visibly append audit events in the inspected functions. Audit logging should be server-side and append-only, with authorization and failure behavior explicitly defined.

### GitHub integration

- `src/lib/github.functions.ts` routes GitHub API calls through the Lovable connector gateway.
- Tokens are read server-side from `LOVABLE_API_KEY` and `GITHUB_API_KEY`; they are not exposed by the inspected browser component.
- Available server functions include viewer/repository listing, repository overview, directory/file reads, file saves, branch creation, and pull-request creation.
- Mutating functions require owner middleware. File writes accept an optional SHA to guard against overwriting a changed file.
- These functions are useful for a controlled source-workflow UI, but do not establish the canonical Lovable project's own connected GitHub remote.

## Safe implementation sequence

1. Confirm the exact canonical Lovable GitHub repository and branch through the project's source-control settings or an authoritative connection response.
2. Create/confirm an isolated development branch on that exact remote; do not write to `main`.
3. Implement the Oneaiplus brand-label cleanup and tests as a small, reversible first code change.
4. Design persistent chat conversations/messages with user ownership, RLS, retention/deletion behavior, and migration rollback before enabling writes.
5. Unify donor section-scoped records with canonical persistence; avoid parallel duplicate tables.
6. Add server-side append-only audit events to state-changing operations.
7. Implement Connectors, MCP Servers, and MCP Registry as separate permissioned subsystems; catalog availability is not connection or execution.
8. Keep normal `/api/chat` independent from XParallel private execution and its approval/revocation gates.

## Explicit non-actions and constraints

- No Lovable AI builder turn was invoked.
- No source files or database tables were changed.
- No migrations were applied.
- No commits were pushed to the Lovable-connected branch because its exact remote is not confirmed.
- No merge to `main`, production deployment, publication change, Render connection, or Vercel connection occurred.
- Donor projects remain unchanged.
- NexAI and IDEAS remain independent products.
