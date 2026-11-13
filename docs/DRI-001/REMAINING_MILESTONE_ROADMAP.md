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
Create provider-neutral runtime adapters, tool contracts, context budgets, model selection, structured outputs, failure handling and evaluation harnesses. Provider credentials remain server-side and optional; zero-cost/local mode must remain viable.

### M3.3 — Parallel Intelligence collaboration
Implement bounded specialist delegation, attributable contributions, independent verification, disagreement resolution, synthesis, budgets and human approval. Measure task quality rather than treating agent count as intelligence.

### M3.4 — Omni orchestration
Connect planning, scheduling, routing, retries, policy checks, approval gates and execution receipts through typed workflows. Every external or consequential action must use the same server-side enforcement boundary.

### M3.5 — Parallel Verse persistent environments
Integrate workspace-scoped spaces, entities, conversations, tasks and event histories with durable storage, access control, lifecycle management and multi-entity isolation. The existing SQLite/optional PostgreSQL prototype is not yet a deployed persistent universe.

### M3.6 — Interoperability and developer conformance kit
Publish versioned SDKs, reference clients, test vectors, protocol compatibility rules, sandboxed sample entities, conformance tests and migration policy. Demonstrate that an independently authored entity can register, communicate and collaborate under the same governance rules.

### M4.1 — Evolution and learning laboratory
Add evaluation datasets, reproducible experiments, versioned proposals, human review, staged rollout, rollback, regression detection and provenance. No autonomous self-modification or silent capability promotion.

### M4.2 — Reality interface
Design permissioned connectors to external services and devices with explicit scopes, operator consent, safety interlocks, simulation-first testing and emergency revocation. Physical-world actions remain disabled until independent safety validation.

### M5 — System integration and independent security validation
Integrate components behind stable interfaces, perform threat modeling, dependency and supply-chain review, penetration testing, disaster recovery, privacy review, accessibility checks, performance and load tests, and independent conformance review. Resolve all critical/high findings before any release proposal.

### M6 — Release-readiness dossier
Produce a component-by-component evidence register, operational runbooks, cost and hosting analysis, backup/restore proof, incident response, governance terms, user documentation, API compatibility guarantees and explicit release blockers. A release recommendation is not a deployment authorization.

## Cross-cutting completion rules

- Keep all work on isolated development branches; do not merge to main.
- No production deployment, domain/DNS change, purchase, paid service, or external commitment without separate explicit approval.
- Keep NexAI and IDEAS independent.
- Preserve existing repositories, histories, identities, routes and integrations.
- Mark every capability as verified, partial, experimental, documented-only, blocked, or unverified based on observable evidence.
- Do not equate passing unit tests with production readiness, safety, general intelligence, or consciousness.
- A milestone is complete only when its code, documentation, tests, CI evidence, limitations and acceptance criteria are all recorded.
