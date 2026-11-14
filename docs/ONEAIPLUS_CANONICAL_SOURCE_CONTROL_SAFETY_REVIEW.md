# Oneaiplus Canonical Source-Control Safety Review

Date: 2026-11-15
Project inspected directly in Lovable: Oneaiplus
Project ID: c2232890-a16d-4289-b2f8-c8de6365a7b4
Inspected commit: 3fac96efc001f394622301568f2f42417c08a87a
Status: Read-only source review; no application files changed.

## Scope and evidence

The canonical Lovable project was inspected through its project and file-reading interface at the exact commit above. Files reviewed:
- src/lib/github.functions.ts
- src/lib/owner.functions.ts
- src/lib/owner-access.ts
- src/integrations/supabase/auth-middleware.ts
- src/components/HomeChat.tsx
- src/server/chat.server.ts
- src/lib/sections.ts
- drizzle/migrations/0000_oneai_owner_access.sql
- drizzle/migrations/0001_owner_project_dashboard.sql
- drizzle/migrations/0002_owner_memories_and_audit.sql
- drizzle/schema.ts

This confirms access to the canonical Lovable source. It does not establish which GitHub repository/branch Lovable synchronizes with; the in-app GitHub connector and Lovable source-control remote remain separate concepts.

## Findings

### 1. GitHub file writes do not enforce the isolated-branch policy

The saveFile server function accepts caller-supplied owner, repo, branch, path, and content. It validates basic lengths and requires the Oneaiplus owner, but it does not:
- deny the repository default branch or main;
- require a branch with an approved isolated-development prefix;
- verify the target branch is not protected;
- require a second confirmation or approval for sensitive paths;
- append an audit event for the write.

This is a high-priority policy gap because the established project rule is no writes to main, no production deployment, and isolated development only. Owner authentication is not a substitute for branch governance.

### 2. Branch creation is not restricted to the approved namespace

The createBranch function validates the proposed branch name syntax and creates a ref from a source branch, but does not enforce a dedicated Oneaiplus development namespace. It should reject protected/default branch targets as write destinations and create branches only under an explicit allowlist, for example oneaiplus/*.

### 3. Pull-request creation is not an execution approval

The createPull function opens a PR using caller-supplied head and base refs. Opening a PR is not merging, but the server function does not check that the head is an approved development branch or that the base is the intended review branch. Keep merge, deployment, and release actions out of this flow.

### 4. Existing auth boundary is useful but incomplete for governance

All reviewed GitHub functions use requireOwner, which validates the Supabase bearer token and calls is_oneai_owner(). Credentials are read server-side from environment variables. This is a useful authentication boundary. It does not by itself enforce the user's no-main/no-production rules.

### 5. Chat is authenticated but not persistent

HomeChat posts to /api/chat, obtains the current Supabase access token, and stores messages only in the component's local useChat state. The UI explicitly says the chat clears when leaving the page. handleChat validates the user and owner status, bounds the message array to 1–100, and streams through the Lovable AI Gateway. The AI Gateway can still reject requests for missing credits; model identifiers are not proof of service availability.

### 6. Database migration source is Drizzle migrations, not the blank schema stub

The canonical project contains three SQL migrations under drizzle/migrations/. drizzle/schema.ts is intentionally blank. Any new migration must be additive and must not invent a Drizzle schema snapshot or overwrite the existing migration history. The exact deployed database must be compared against these migrations before applying anything.

### 7. Audit events are not transactionally coupled to mutations

The existing audit table has owner-scoped SELECT and INSERT policies, with no authenticated UPDATE/DELETE policies in the reviewed migration. Current server code writes audit events separately after some mutations and ignores audit insert errors in a helper. This can leave a successful mutation without its expected audit record. Future security-sensitive mutations should use a transaction/RPC or explicitly report audit failure.

### 8. Identity labels remain inconsistent

The canonical project is named Oneaiplus in Lovable metadata, but reviewed UI/chat copy still says OneAI. This is a source-level identity cleanup item, not a database blocker.

## Required remediation before enabling source-control writes

1. Add a server-side branch policy helper shared by saveFile, createBranch, and createPull.
2. Deny writes to main, the default branch, protected branches, and all branches outside an approved isolated prefix.
3. Verify branch metadata server-side immediately before each write; do not rely on disabled UI controls.
4. Require an explicit allowlist for repositories and paths if the Builder is intended to operate only on approved projects.
5. Add server-side audit records for branch creation, file writes, and PR creation. Fail closed if the audit write fails, or move the operation into an atomic server-side workflow.
6. Add tests for main/default/protected branch rejection, unapproved branch rejection, allowed isolated branch success, path bounds, stale SHA conflicts, and unauthenticated/non-owner rejection.
7. Keep merge and deploy operations separate and disabled until a distinct release-approval workflow exists.

## Chat and persistence implementation notes

- Preserve /api/chat as the normal chat endpoint; do not route ordinary chat through XParallel public /public/ask.
- Add conversation and message persistence through owner-scoped tables and server functions, using the separate migration proposal.
- Do not store provider credentials, bearer tokens, or secrets in message content/metadata.
- Do not change the existing chat provider or claim the model is operational without a successful runtime test.

## Non-actions and release boundary

- Read-only inspection only.
- No source code changed.
- No database query or mutation performed during this review.
- No migrations applied.
- No writes to GitHub project repositories or branches through the Oneaiplus Builder.
- No merge to main and no production deployment.
- Donor projects remain untouched; NexAI and IDEAS remain independent.
- Render and Vercel account-level connection remains deferred.
