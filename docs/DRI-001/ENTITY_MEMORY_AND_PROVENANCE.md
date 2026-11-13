# DRI-001 — Entity memory and knowledge provenance

Status: partial local implementation.

## Implemented
- Workspace/entity-scoped memory records with mandatory host authentication and per-action authorization callbacks.
- AES-256-GCM application-level encryption; key material is resolved from a trusted host callback and never stored by this module.
- Authenticated associated data binds ciphertext to workspace, entity and memory ID.
- Provenance records source type/reference/digest, content digest, creator and timestamp.
- Bounded retention (60 seconds to one year), expiry cleanup on search, exact deletion and authorized export.
- Lexical retrieval with bounded results and a small precision/recall/reciprocal-rank evaluation helper.
- Tests cover encryption-at-rest behavior, provenance, retrieval, access denial, integrity tampering, deletion and evaluation metrics.

## Not yet operational
- No production key-management service, key rotation/recovery or hardware-backed custody.
- No integration with the existing chat/memory routes or existing workspace memory vault.
- No semantic embedding index, retrieval benchmark corpus, retention scheduler or independently verified deletion from backups/replicas.
- No cross-device sync, distributed storage or independent privacy/security review.
- No automatic secret/credential detection; users and host ingestion policies must prevent secrets from entering memory.

Memory encryption and permissions depend on correctly implemented host key and authorization adapters. A local SQLite database is not a tamper-proof or distributed memory service.
