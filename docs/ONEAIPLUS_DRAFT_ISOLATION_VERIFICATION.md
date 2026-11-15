# Oneaiplus Draft Isolation Verification

Date: 2026-11-15

## Scope

This record checks whether the existing Lovable development draft is safe for database-backed implementation. It does not modify application code, project configuration, database state, or deployment settings.

## Verified project state

- Canonical project: `Oneaiplus`
- Project ID: `c2232890-a16d-4289-b2f8-c8de6365a7b4`
- Canonical project remains published.
- Canonical project latest commit observed: `3fac96efc001f394622301568f2f42417c08a87a`
- Draft ID: `drft_01m7dd5s71fb6t2a847pk89zgf`
- Draft status: `ready`
- Draft backend metadata: `local_supabase`
- Draft base SHA: `3fac96efc001f394622301568f2f42417c08a87a`
- Draft edit history: zero edits returned.
- Canonical cloud database status: enabled, stack `supabase`.

## Safety conclusion

The available metadata does not prove that the draft has an independent database. The canonical project's cloud database is enabled, while the draft reports a local Supabase backend. There is no draft-scoped database-status or database-query action exposed in the available interface, and the draft has no edits that could demonstrate an isolated database binding.

Therefore, database-backed implementation is blocked until isolation can be positively established.

## Prohibited until isolation is proven

- Do not apply conversation, message, memory, or audit migrations through the canonical project.
- Do not run INSERT, UPDATE, DELETE, or DDL against the canonical database for draft testing.
- Do not accept/merge the draft merely to gain an editing route.
- Do not use the live project's message action as a substitute for a draft-targeted action.
- Do not deploy or merge to production/main.

## Safe next steps

1. Obtain a supported draft-targeted code-edit operation, or create an explicitly isolated development copy with a separately verified database.
2. Verify database identity using non-secret project/database metadata before any write.
3. Implement conversation persistence with owner-scoped row-level security and audit consistency.
4. Test cross-user access denial, retry/idempotency, malformed payloads, and provider/database failure paths.
5. Keep the implementation on an isolated development branch and preview only.

## Evidence boundary

This is a verification record, not an implementation claim. No application code or database data was changed by this check.
