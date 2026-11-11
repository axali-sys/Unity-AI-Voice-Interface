# ƎllE Intelligence Architecture and Omni Knowledge Genome

## Scope
This branch introduces service-layer foundations without replacing the existing chat gateway, memory vault, conversation store, provider catalog, or XParallel roaming services.

## Responsibility boundaries
- OneAI: unified workspace.
- ƎllE: task understanding, planning, state transitions and decisions.
- Omni: knowledge records, source metadata, version history and verification evidence.
- Parallel Intelligence: collaborative reasoning through configured providers.
- XParallel: authenticated interoperability and task transport.
- AROT: provenance and audit evidence.

## Files
- `xparallel/omni_genome.py`: SQLite-backed workspace-scoped records, source metadata, immutable version rows, verification evidence and events.
- `xparallel/elle_lifecycle.py`: SQLite-backed task lifecycle, transitions, human approval gate and verification evidence.
- `tests/test_omni_genome.py`: focused Omni service tests.
- `tests/test_elle_lifecycle.py`: focused ƎllE lifecycle tests.

## Storage
SQLite is the default. `OMNI_DB` and `ELLE_DB` may override database paths. Both default to `oneai_omni.sqlite3`. No paid dependency is introduced.

## State semantics
Omni records begin as `received` and `unverified`. Verification requires a method, actor, result and non-empty evidence. Model-originated records are never automatically verified.

ƎllE tasks begin at `UNDERSTAND`. High and critical risk tasks automatically require approval. The lifecycle service records authorization but does not itself execute arbitrary code.

## Security boundary
These are service modules, not authentication middleware. HTTP adapters must derive actor and workspace identity from authenticated context, enforce workspace membership, and only pass `authorized=True` after checking a human principal's permission. Never trust a client-provided workspace or approval boolean.

## HTTP integration status
- `xparallel/enterprise_auth.py` now verifies the `X-Enterprise-Identity` short-lived token and applies role-based authorization to ƎllE, Omni, Parallel Research and XParallel dispatch routes.
- Workspace and actor values for these routes are derived from signed claims; request-body and query-string identity fields are ignored.
- `XP_TOKEN` remains a machine/service credential and is not treated as a human identity.
- The server-side issuer primitive must only be called after upstream human authentication and authoritative workspace membership validation.
- No upstream login adapter or membership service is yet connected. These routes fail closed without a valid signed identity token; end-user activation is therefore not complete.

## Not yet complete
1. Trusted login adapter and authoritative workspace-membership lookup/token issuance.
2. Integration with existing memory and conversation retrieval, including shared tenant context.
3. OneAI UI for task and knowledge history and login-to-token flow.
4. End-to-end tests and real runtime verification across UI, API and SQLite.
5. Retention, deletion, migration, backup and concurrency review.

Do not describe this branch as production-ready or end-to-end operational until these items are implemented and verified.
