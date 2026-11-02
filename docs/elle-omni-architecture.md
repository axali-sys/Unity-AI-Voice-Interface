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

## Not yet complete
1. Authenticated HTTP routes in `xparallel/server.py`.
2. Adapter to existing `workspace_context`, authz and AROT audit repository.
3. Integration with existing memory and conversation retrieval.
4. OneAI UI for task and knowledge history.
5. End-to-end tests and runtime verification.
6. Retention, deletion, migration, backup and concurrency review.

Do not describe this branch as production-ready or end-to-end operational until these items are implemented and verified.
