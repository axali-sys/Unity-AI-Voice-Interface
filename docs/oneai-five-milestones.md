# OneAI five foundational milestones — delivery and verification

This report separates committed service capabilities from capabilities that still need integration or live verification.

## 1. ƎllE Intelligence Architecture
The task service in `xparallel/elle_lifecycle.py` stores objective, expected outcome, workspace, owner, constraints, knowledge references, capabilities, risk, state, approval and verification. High/critical tasks require explicit approval. The service does not execute arbitrary code. HTTP routes and AROT event hooks are mounted in the existing XParallel server.

## 2. Omni Knowledge Genome
`xparallel/omni_genome.py` stores workspace-scoped records, source references, version history, verification evidence and events in SQLite. Records begin received/unverified. Model-origin records are not automatically verified. HTTP create/read/search/history/verify routes are mounted.

## 3. Parallel Intelligence
`xparallel/parallel_intelligence.py` now supports an independent two-provider panel when both primary and secondary HTTPS OpenAI-compatible endpoints, keys and models are configured. The primary uses `XP_AI_CHAT_COMPLETIONS_URL`, `XP_AI_API_KEY`, `XP_AI_MODEL`; the optional secondary uses `XP_AI_SECONDARY_CHAT_COMPLETIONS_URL`, `XP_AI_SECONDARY_API_KEY`, `XP_AI_SECONDARY_MODEL`. Provider IDs may be set with `XP_AI_PROVIDER_ID` and `XP_AI_SECONDARY_PROVIDER_ID`. Each model receives the same research question independently. Results are returned separately; the service does not claim consensus, external verification or execution. With fewer than two configured providers, it fails closed to a non-panel status.

## 4. XParallel Interoperability
`xparallel/interoperability_protocol.py` exposes credential-free agent passports and discovery over the existing roaming registry. Dispatch accepts only allowlisted task types and requires both an approval signal and the configured execution approval header at the HTTP boundary. The roaming worker registry remains the task transport.

## 5. AROT Evidence
`xparallel/arot_evidence.py` writes entity-linked event evidence through the existing audit repository. ƎllE and Omni route operations emit AROT records. This is an adapter over the current audit ledger, not yet a formally immutable or externally anchored evidence chain.

## Security and production boundary
The backend still uses a shared bearer token and request-provided workspace identifiers. The current implementation does not establish per-user identity, workspace membership, or tenant-bound credentials. Do not expose this API directly as a multi-tenant production service until identity-bound workspace authorization is implemented. The UI and server must not trust a client-supplied approval boolean.

## Remaining work before production
- Bind authenticated user identity and workspace membership to every API operation; remove caller-controlled workspace trust.
- Integrate these routes into the existing OneAI UI with real loading/error/empty states and no simulated actions.
- Add authenticated HTTP end-to-end tests across task creation, knowledge storage/retrieval, approvals, verification and audit evidence.
- Add retention/deletion, backup/restore, migration and concurrency controls.
- Configure two real provider endpoints and verify the panel with authorized credentials; unit tests alone do not prove live provider access.
- Perform deployment-specific health/auth checks and security review.

No main-branch merge or production deployment is authorized by this work.