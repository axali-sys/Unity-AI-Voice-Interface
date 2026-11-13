# DRI-001 — Remaining Milestone Roadmap

Status: living engineering plan; milestone acceptance is evidence-based. This roadmap does not authorize merge, production deployment, paid services, or changes to independent products.

## Completed foundations

- M1: architecture baseline, repository/prototype audit, 113-component and 15-preservation-identity coverage snapshot.
- M2.1–M2.8: Digital DNA schema/registry prototype, Ed25519 identity and key lifecycle, deny-by-default action policy, signed message envelopes, local policy-gated message gateway, governance/permission registry, capability verification laboratory.
- M2.9: verified entity action gate composing trusted identity context, exact artifact-bound capability evidence, and approved exact-scope grants. The gate decides only; it does not execute.
- M2.10: restricted Docker execution-boundary hardening, strict resource-setting validation, local digest-only image use, bounded concurrent stdout/stderr capture, and runner process-group timeout cleanup are implemented in the isolated branch. Unit/CI verification is required on the latest head; no live Docker hostile-code test or daemon-side container cleanup test has been performed.

## Remaining milestones and acceptance gates

### M2.11 — Trusted host adapters and enforcement boundary
**Partial implementation:** `xparallel/trusted_host_adapters.py` now composes the existing Digital DNA, Ed25519 key, governance grant, capability-evidence and decision-gate repositories. Authentication and immutable artifact provenance are mandatory injected host trust roots. The adapter derives workspace/entity/key/owner state from scoped server-side repositories and never trusts a manifest capability status or client-supplied artifact digest. Local tests cover registry-backed resolution, proof-of-possession key activation, invalid authentication, workspace isolation and missing trusted artifact metadata. CI now includes this test module.

**Not complete / hard gate:** no real authentication provider or authoritative artifact store is configured; the adapter is not connected to HTTP routes; route-level integration tests against a trusted host remain outstanding. The current shared bearer-token/client-workspace HTTP model is not sufficient to activate this path. Consequential execution remains disabled.

### M2.12 — Execution approval, job lifecycle and revocation
**Implemented and CI-tested locally:** `xparallel/execution_approval.py` creates immutable job intents bound to payload/artifact/runner digests, exact action/resource scope and bounded limits; requires a separate approver; issues a one-time hashed ticket; enforces expiry, executor identity, cancellation, terminal outcomes, and injected revocation/current-state checks at start, runtime checkpoints and successful completion. CI run `43459692943` passed all XParallel integration-test steps, including the new lifecycle tests. The executor is not connected, and cancellation/revocation are only enforceable if a future runner polls the checkpoint and stops. No work is launched by this registry.

### M2.13 — Execution evidence and provenance
**Implemented and CI-tested locally:** `xparallel/execution_receipts.py` builds receipts from an authoritative terminal job record, binding intent/payload/artifact/runner digests, human approval, policy grant and verification run, timestamps, exit status, bounded resource use and evidence references. Receipts are SHA-256 hash-chained per workspace and signed through an injected host signer; chain verification checks continuity and signatures. CI run `43460102868` passed all XParallel integration-test steps, including the new receipt tests. SQLite triggers reject ordinary row updates/deletes, but local DB state is not immutable against privileged tampering. No external anchor, evidence artifact store, or live executor integration exists yet.

### M2.14 — Durable storage and recovery
**Local foundation implemented and CI-tested; subsystem migration incomplete:** `xparallel/storage_recovery.py` adds a transactional SQLite store, ordered/checksummed migrations, workspace-scoped JSON repository, online backup with integrity check, approval-gated restore with pre-restore safety copy, and prefix-scoped backup retention. CI run `43460448525` passed all XParallel integration-test steps, including the storage/recovery tests. Existing Digital DNA, identity, governance, messaging, verification, execution and receipt stores have not all been moved behind this interface. No distributed backend, off-site backup, encryption-at-rest or disaster-recovery rehearsal is configured.

### M2.15 — Secure network transport and distributed messaging
**Partial implementation:** `xparallel/secure_transport.py` adds AES-256-GCM encryption for signed envelopes, authenticated packet headers bound to workspace/recipient/key ID, and a local SQLite outbox with idempotent enqueue, per-sender pending quotas, bounded retry/dead-letter behavior, rate limiting, injected acknowledgement verification and per-attempt authorization/revocation checks. `tests/test_secure_transport.py` covers encryption, tamper/wrong-key rejection, idempotency, acknowledgement, retry/dead-letter, revocation and quota behavior. See `docs/DRI-001/SECURE_NETWORK_TRANSPORT.md`.

**Not operational / hard gates:** no secure key agreement or distribution, TLS peer authentication, cryptographically implemented acknowledgement verifier, distributed queue/leases, cross-node revocation propagation, complete schema negotiation, gateway/API integration or multi-node conformance tests. SQLite outbox is local state, not a distributed message fabric. No live network delivery is enabled.

### M2.16 — Entity discovery and federation
**Partial implementation:** `xparallel/entity_federation.py` adds owner-authorized Ed25519-signed local registry records, active-key verification, public/allowlist/private visibility, injected peer-trust policy, protocol major-version compatibility, exact declared-capability filtering, bounded results, query rate limiting, expiry and owner-authorized revocation. Capability declarations are explicitly not verification. Tests cover signatures, visibility, owner binding, compatibility, revocation, wrong-key rejection and rate limits. See `docs/DRI-001/ENTITY_DISCOVERY_AND_FEDERATION.md`.

**Not operational:** no network registry, cross-organization replication, trust-authority hierarchy, transparency log, distributed anti-enumeration controls, revocation propagation, route integration or independent registry conformance suite exists.

### M3.1 — Entity memory and knowledge provenance
**Partial implementation:** `xparallel/entity_memory.py` adds workspace/entity-scoped encrypted memory, mandatory host authentication and per-action authorization adapters, AES-256-GCM encryption with host-resolved keys, authenticated context binding, source/content provenance, bounded retention, authorized export/deletion, lexical retrieval and precision/recall/reciprocal-rank evaluation metrics. Tests cover encrypted storage, provenance, access denial, tampering, deletion and retrieval metrics. See `docs/DRI-001/ENTITY_MEMORY_AND_PROVENANCE.md`.

**Not operational:** no production key-management service, route/chat integration, semantic index, benchmark corpus, scheduled retention service, deletion verification across backups/replicas, cross-device sync or independent privacy/security review. Existing memory vaults have not been migrated. Host ingestion must prevent credentials from entering memory.

### M3.2 — Cognitive runtime and model gateway
**Partial implementation:** `xparallel/cognitive_runtime.py` adds a provider-neutral gateway, explicit provider selection, local-first Ollama adapter restricted to loopback, context/output budgets, structured JSON schema checks, authorized tool proposals (never executed), and a deterministic evaluation harness. Tests cover provider selection, budgets, structured output, tool authorization, evaluation and loopback restrictions. See `docs/DRI-001/COGNITIVE_RUNTIME_AND_MODEL_GATEWAY.md`.

**Not operational:** no live local model was queried; existing chat routes are not migrated; no streaming/cancellation, production model policy, token accounting, context management, verified execution integration, benchmark corpus or independent prompt-injection review exists. No paid provider is selected by default.

### M3.3 — Parallel Intelligence collaboration
**Partial implementation:** `xparallel/parallel_intelligence.py` adds bounded sequential specialist delegation, attributable content/evidence digests, a mandatory independent verifier, synthesis from verified contributions only, conflict escalation, and strict task/context/output budgets. Every result requires human review; no tool execution occurs. Tests cover attribution, verification failure, conflicts and budgets. See `docs/DRI-001/PARALLEL_INTELLIGENCE_COLLABORATION.md`.

**Not operational:** no model specialists, durable queue, concurrency scheduler, cancellation/timeouts, token/cost accounting, evidence validation service, quality benchmark, review UI, approval-ticket binding or verified execution integration exists. Conflict detection is supplied by the synthesis adapter and is not independently calibrated.

### M3.4 — Omni orchestration
**Partial implementation:** `xparallel/omni_orchestrator.py` adds typed workflow validation, dependency ordering, cycle rejection, mandatory policy authorization, human approval-ticket verification for consequential steps, bounded idempotent retries, dependency stop behavior and mandatory receipt recording. Tests cover authorization, approval, retries, receipt failures and dependencies. See `docs/DRI-001/OMNI_ORCHESTRATION.md`.

**Not operational:** no durable scheduler/queue, worker leases, resume/recovery, connection to existing planners/Parallel Intelligence/execution-ticket/receipt stores, real approval UI/provider, configured executor, timeout/cancellation, concurrency, observability or production integration exists. Host adapters must enforce the verified action gate; the orchestrator is not itself a trust authority.

### M3.5 — Parallel Verse persistent environments
**Partial implementation:** Reused the existing unmerged PR #44 SQLite world store and tests on this isolated branch. Added `xparallel/parallel_verse_service.py`, which derives workspace identity from an injected authenticated session and applies per-action ACL checks; client-supplied workspace selection is not accepted. Agent, space, task and event records retain workspace isolation and restart persistence tests. See `docs/DRI-001/PARALLEL_VERSE_PERSISTENT_ENVIRONMENT.md`.

**Not operational:** no trusted HTTP route integration, production identity provider, durable deployed database, PostgreSQL adapter/migrations integration in this branch, per-space membership ACLs, lifecycle update/delete, scheduler/worker leases, multi-node persistence, or unified conversation/entity-memory transactions. Tasks are records, not executing jobs. The PR #44 remains separate and unmerged.

### M3.6 — Interoperability and developer conformance kit
**Partial implementation:** Added `xparallel/sdk.py` reference client for signed/encrypted entity messages, `xparallel/protocol_compat.py` deterministic version negotiation, a versioned message JSON Schema, an independent-entity manifest example and executable conformance tests. Tests demonstrate two independently keyed entities exchanging an encrypted signed message, recipient binding, replay rejection and protocol negotiation. See `examples/xparallel/conformance/README.md`.

**Not operational:** SDK is in-process and performs no network delivery. No published package/SDK release, external developer documentation, sandbox distribution, migration tooling, cross-organization conformance, trusted key exchange, live federation, or end-to-end collaboration through production governance is demonstrated.

### M4.1 — Evolution and learning laboratory
**Partial implementation:** `xparallel/evolution_lab.py` adds authenticated workspace-scoped experiment records with canonical dataset/config digests, baseline/candidate evaluation adapters, regression-gated proposals, separate human approval checks for staging and promotion, lifecycle event history, and rollback state records. Tests cover approval, regression blocking, workspace isolation and record-only rollback. See `docs/DRI-001/EVOLUTION_AND_LEARNING_LAB.md`.

**Not operational:** no model training, trusted dataset registry, signed experiment runner, benchmark governance, canary traffic, live promotion/deployment, actual runtime rollback, telemetry/drift detection or independent reproducibility review. Promotion and rollback are records only; autonomous self-modification is not enabled.

### M4.2 — Reality interface
**Partial implementation:** `xparallel/reality_interface.py` adds authenticated workspace-scoped connector registration, exact non-wildcard scopes, short-lived operator consent, simulation-only actions, payload/result digests, audit events, expiry and emergency revocation. Tests cover consent, scope, expiry, workspace isolation and revocation. See `docs/DRI-001/REALITY_INTERFACE_SAFETY_BOUNDARY.md`.

**Not operational / hard gate:** no external service/device connector, network transport, hardware interlock, operator UI, production identity/consent provider, route integration or independent safety case exists. No real-world execution method is provided; physical-world actions remain disabled.

### M5 — System integration and independent security validation
**Documentation foundation added:** `docs/DRI-001/SECURITY_THREAT_MODEL.md` records assets, trust boundaries, 16 threat classes, release-blocking controls and a staged validation plan. `docs/DRI-001/INTEGRATION_ACCEPTANCE_MATRIX.md` records cross-subsystem integration evidence requirements, current blockers and a fail-closed acceptance sequence.

**Not complete / release blocked:** this is a threat-model draft, not an independent security assessment. No full cross-module production integration, trusted identity provider, API-level tenant isolation proof, live executor integration, multi-node transport/federation, hostile-code red team, independent penetration test, SBOM/vulnerability review, disaster-recovery rehearsal, privacy/accessibility/performance review or external conformance audit has been completed. Critical/high findings cannot yet be declared closed.

### M6 — Release-readiness dossier
**Draft evidence dossier created:** `docs/DRI-001/RELEASE_READINESS_DOSSIER.md` records project boundaries, evidence classifications, milestone status, CI references, release blockers, cost posture and sign-off checklist. It explicitly recommends **DO NOT RELEASE / DO NOT DEPLOY**.

**Not complete:** the 113-component source-to-code audit, operational runbooks, independent security sign-off, cost/hosting analysis, backup/restore rehearsal, incident response, governance/legal terms, full user documentation, API compatibility guarantees and external conformance evidence remain outstanding. The dossier must be refreshed against the exact candidate release commit. A release recommendation is not deployment authorization.

## Cross-cutting completion rules

- Keep all work on isolated development branches; do not merge to main.
- No production deployment, domain/DNS change, purchase, paid service, or external commitment without separate explicit approval.
- Keep NexAI and IDEAS independent.
- Preserve existing repositories, histories, identities, routes and integrations.
- Mark every capability as verified, partial, experimental, documented-only, blocked, or unverified based on observable evidence.
- Do not equate passing unit tests with production readiness, safety, general intelligence, or consciousness.
- A milestone is complete only when its code, documentation, tests, CI evidence, limitations and acceptance criteria are all recorded.
