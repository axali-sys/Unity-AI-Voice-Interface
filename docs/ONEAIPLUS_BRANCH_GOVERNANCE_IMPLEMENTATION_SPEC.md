# Oneaiplus Branch Governance Implementation Specification

Date: 2026-11-15
Status: Implementation specification only; no application code or database changed.

## Decision

All Oneaiplus Builder write operations must be restricted to explicitly approved isolated development branches. Authentication as the project owner is necessary but not sufficient. The server must enforce branch policy before every GitHub write.

## Approved default policy

- Allowed development branch prefix: oneaiplus/
- Denied branch names: main, master, production, release, and the repository's default branch.
- Deny protected branches regardless of their name.
- Do not permit a caller to override policy with a client-supplied boolean.
- Do not provide merge, deployment, release, or branch deletion operations in this milestone.
- Repository allowlisting should be configured server-side; until configured, Builder writes should fail closed.
- The existing user-approved development branch oneaiplus/unification-foundation-2026-11-14 may be read and reviewed, but the application must not assume it is the canonical Lovable sync branch.

## Required server flow

For saveFile:
1. Require owner authentication.
2. Validate owner/repository against a server-side repository allowlist.
3. Fetch repository metadata and the exact target branch from GitHub.
4. Reject if target equals default branch, is protected, is in the denylist, or does not start with oneaiplus/.
5. Validate path against a server-side allowlist/denylist. Reject credential files, workflow/deployment configuration and security policy files unless explicitly approved.
6. Require an existing file SHA for updates; use GitHub's SHA conflict protection.
7. Write file.
8. Append a redacted audit event. If the audit write fails, surface a failure and create a reconciliation record; do not claim the operation is fully audited.

For createBranch:
1. Require owner authentication and repository allowlisting.
2. Require new branch name to start with oneaiplus/.
3. Fetch source ref and reject protected/default source refs unless a narrowly approved base is configured.
4. Ensure destination ref does not already exist.
5. Create branch and audit the operation.

For createPull:
1. Require owner authentication and repository allowlisting.
2. Require head to start with oneaiplus/.
3. Require base to equal the configured review base (normally main); PR creation is allowed for review, but merging is not.
4. Fetch both refs and ensure they exist.
5. Create PR and audit it.
6. Never auto-merge, auto-deploy, or change branch protection.

## Path controls

Default deny for:
- .env and any .env.* files
- private keys, certificates, tokens and credential dumps
- deployment secrets and environment configuration
- production workflow files
- Supabase production migrations or config until a separately approved migration process exists
- generated lockfiles/package manifests that change dependencies unless the change is reviewed
- repository policy files (CODEOWNERS, branch protection automation) without explicit approval

Allow source and documentation changes only within the approved development branch and repository allowlist.

## Audit event minimum

Record:
- actor user ID
- operation (branch_create, file_write, pull_request_create)
- repository full name
- source and destination branch
- file path when relevant
- resulting commit SHA or PR number
- timestamp
- request correlation ID

Never record access tokens, connector credentials, file contents, or secret values.

## Test matrix

| Scenario | Expected result |
|---|---|
| Anonymous request | 401 |
| Authenticated non-owner | 403 |
| Owner writes to main | Deny |
| Owner writes to default branch | Deny |
| Owner writes to protected branch | Deny |
| Owner writes outside oneaiplus/ | Deny |
| Owner writes to approved isolated branch | Allow after repo/path checks |
| Owner creates branch outside oneaiplus/ | Deny |
| Owner opens PR from non-approved head | Deny |
| Owner opens PR to unapproved base | Deny |
| Owner updates file with stale SHA | Conflict; no overwrite |
| Repository not allowlisted | Deny |
| Path matches secret/deployment denylist | Deny |
| Audit write unavailable | Report incomplete/failed audit; no success claim |

## Acceptance gates

- Unit tests cover branch and path policy independently of UI.
- Integration tests use a disposable GitHub test repository.
- Tests demonstrate no write can target main/default/protected branches.
- Tests demonstrate allowed isolated-branch writes work.
- Audit events are redacted and verifiable.
- No merge or deployment action is introduced.
- Preview is reviewed before any draft acceptance.
- Production remains unchanged.

## Next application implementation sequence

1. Add pure branch/path policy helpers and unit tests.
2. Add server-side repository allowlist and branch metadata checks.
3. Apply policy to saveFile, createBranch, and createPull.
4. Add redacted audit writes and reconciliation handling.
5. Rename user-visible OneAI labels to Oneaiplus without changing internal stable identifiers or route slugs.
6. Run typecheck, lint, unit tests, and preview smoke tests.
7. Keep changes isolated; do not accept the draft into the live project until explicitly reviewed.

## Explicit non-actions

No application source code has been modified. No database writes or migrations were performed. No GitHub repository files were changed through the Builder. No merge to main, production deployment, paid service, or donor project mutation occurred.
