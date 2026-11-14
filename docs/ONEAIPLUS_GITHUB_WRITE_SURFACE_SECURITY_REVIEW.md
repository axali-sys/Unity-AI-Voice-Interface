# Oneaiplus GitHub Write-Surface Security Review

Date: 2026-11-15
Canonical source inspected: Lovable project c2232890-a16d-4289-b2f8-c8de6365a7b4
Inspected ref: 3fac96efc001f394622301568f2f42417c08a87
File: src/lib/github.functions.ts
Review type: Read-only source inspection; no live calls or write tests.

## Summary
The GitHub server functions require canonical owner middleware, validate basic input shapes and keep GitHub credentials server-side. However, their write APIs do not enforce the required isolated-development policy.
Owner authentication answers who may call the functions; it does not constrain which repository, branch, path or base branch that owner may modify.

## Verified findings

### 1. saveFile accepts any caller-supplied branch
The input schema accepts branch as any non-empty string. The handler sends it directly to the GitHub Contents API. There is no server-side requirement for the oneaiplus/ prefix, nor rejection of main, default, protected or release branches. The optional SHA is a useful stale-file guard when supplied, but is not branch authorization and is optional.
Impact: an owner caller can request a write to a protected or production branch if the GitHub credential permits it.

### 2. createBranch accepts arbitrary branch names and source refs
The name schema permits a broad character set but does not enforce the oneaiplus/ prefix. The source branch is caller-supplied and is not checked against a safe base-branch allowlist. Duplicate-ref rejection does not establish that the requested branch is safe.
Impact: the application can create branches outside the agreed development namespace.

### 3. createPull accepts arbitrary head and base refs
The function validates only that head and base are non-empty strings. It does not require a oneaiplus/* head, reject protected bases, or require a fixed review base. It creates a PR but does not merge it.
Impact: the application can open review requests from or into unintended branches. PR creation is not a merge, but its target must still be constrained.

### 4. No explicit audit record for GitHub mutations
The inspected saveFile, createBranch and createPull handlers do not write a canonical audit_events record.
Impact: there is no product-level attributable record of repository, branch, path, operation, outcome and commit/PR identifiers.

### 5. Repository and path scope are not allowlisted
The functions accept arbitrary owner/repo values and repository paths within basic length checks. Owner middleware is not a repository allowlist, and path length validation is not a path policy.
Impact: a connected GitHub credential with broad permissions could be used against unrelated repositories or sensitive paths.

## Positive controls observed
- All inspected GitHub functions use requireOwner middleware.
- Credentials are read server-side from environment variables and are not returned by these functions.
- Inputs use Zod schemas and bounded lengths.
- saveFile includes an optional GitHub SHA to detect stale file content when supplied.
- GitHub operations are mediated through the server-side connector gateway.
- createPull only opens a pull request; no merge operation was found in this file.

## Required remediation before enabling GitHub writes
1. Server-side repository allowlist: permit only an explicitly configured canonical Oneaiplus source repository. Do not assume Unity-AI-Voice-Interface is the canonical Oneaiplus frontend repository; it is the XParallel/backend source.
2. Branch policy: writes only to names matching oneaiplus/<work-item>; reject main, master, default, release, production, protected and all other branch namespaces.
3. Branch source policy: create branches only from a verified, configured development base SHA/ref. Do not accept arbitrary source refs from the browser.
4. PR policy: head must match oneaiplus/*; base must equal the configured review base; prohibit auto-merge and merge endpoints.
5. Path allowlist: restrict writes to approved application paths and deny secrets, environment files, deployment config, workflows, migrations and other sensitive paths unless separately reviewed.
6. Concurrency/staleness: require an expected file SHA for updates, verify branch head has not moved unexpectedly, and fail closed on mismatch.
7. Audit: record actor from verified server context, repository, branch, normalized path, operation, approval reference, result and GitHub commit/PR IDs. Redact tokens and file secrets. Audit failures must prevent a privileged write from being reported as successful.
8. Tests: prove owner denial; arbitrary repo denial; main/default/protected branch denial; non-prefixed branch denial; arbitrary source ref denial; unsafe path denial; missing/stale SHA denial; valid isolated branch success; PR wrong base/head denial; audit success/failure behavior.

## Acceptance criteria
No GitHub write is considered safe until the above checks are enforced server-side and tested. UI controls alone are not sufficient. Do not enable the existing write functions on the basis of owner authentication alone.

## Scope and non-actions
This review does not modify application source, repository settings, branch protection, credentials, connected GitHub repositories, databases or deployments. No GitHub write endpoint was invoked. The inspected source ref remains unchanged.