# OneAI + XParallel: UIDaaS, Jellybox, Omni, and Parallel Verse Architecture

**Status:** Architecture proposal on a development branch. This document does not claim that every component is implemented or production-verified.

## Product principle

- **OneAI is the workspace**: the human-facing command center for asking, researching, planning, building, repairing, reviewing, and approving work.
- **XParallel is the DNA of AI**: the interoperability and execution infrastructure that discovers, connects, coordinates, verifies, and repairs independent AI systems.
- **Parallel Verse is XParallel's persistent digital world**: the environment in which registered agents, spaces, events, memories, and tasks can be represented over time.
- **Omni is the orchestration engine**: it converts a user goal into a bounded plan, routes steps to eligible providers or tools, gathers evidence, and requests approval before consequential execution.
- **Jellybox is the proposed data and SmartBlock execution layer**: it stores and packages approved work units, artifacts, and events; future device-node or consensus functionality must be implemented and separately verified.
- **UIDaaS is the proposed identity, device trust, and access framework**: it binds authenticated users and devices to explicit identities, permissions, workspace membership, and revocable credentials.
- **UnityAI is the assistant/interaction experience**; the name and its history remain preserved within the unified OneAI workspace.

## System context

```text
Human / trusted device
        |
        v
UIDaaS identity + session + device trust
        |
        v
OneAI Workspace / Command Center
  | Assistant | AI Mixer | Build Studio | Repair Shop | Omnibox |
        |
        v
Omni orchestrator (plan -> route -> evidence -> approval -> execute)
        |
        v
XParallel interoperability gateway and policy boundary
        |
        +--> AI model providers / local open-source models
        +--> approved APIs, repositories, builders, and workers
        +--> Parallel Verse world store (agents, spaces, events, tasks)
        +--> Jellybox SmartBlock/artifact store (proposed)
        |
        v
Audit trail + verification report + user-visible outcome
```

This is a logical architecture, not a claim that every arrow is already wired in the current deployment.

## Trust and execution boundaries

1. **Identity first:** resolve the authenticated principal server-side. Do not trust a client-supplied `workspace_id`, `owner_id`, role, or device identity as proof of authorization.
2. **Least privilege:** each agent, provider, tool, device, and worker receives only the scopes required for its assigned task.
3. **Plan before action:** planning, retrieval, and proposed code changes may be read-only by default. External writes, deployments, payments, account changes, and destructive actions require an explicit, auditable approval.
4. **Secrets stay server-side:** provider keys, XP tokens, database URLs, signing keys, and execution approvals must never be rendered into browser code or logs.
5. **Evidence over simulated success:** report provider name/model, status, timestamps, source/artifact references, tests run, skipped checks, and errors. If a service is not configured, return a clear unavailable state.
6. **Workspace isolation:** derive workspace membership from the authenticated identity and enforce it in every query and write. Database constraints should independently reject cross-workspace references.
7. **Reversibility:** version SmartBlocks, skills, policies, and agent configurations. Use review, staged rollout, and rollback; do not claim that model weights autonomously evolve unless a real training/evaluation pipeline exists.

## Component contracts

### UIDaaS — identity and device trust

**Responsibilities**
- User, service, agent, and device identity records.
- Authentication/session lifecycle and credential revocation.
- Device enrollment and optional biometric verification through platform-native mechanisms.
- Role/scope authorization and identity-to-workspace membership.
- Audit events for enrollment, authentication, authorization denial, and revocation.

**Implementation order**
1. Use a proven authentication/session library or provider; do not invent cryptography.
2. Store only required device public-key or attestation metadata. Never store raw biometric data.
3. Bind each identity to server-side workspace membership.
4. Enforce session expiry, rate limits, recovery procedures, and revocation.
5. Add device attestation only where the platform supports it; a UI biometric prompt alone is not proof of server-verified identity.

**Acceptance tests**
- Unauthenticated requests fail closed.
- A valid identity can access only its authorized workspace.
- Revoked/expired credentials fail.
- Device enrollment and recovery are audited.
- Raw biometrics and credentials never enter logs or application tables.

### Jellybox — data, artifacts, and SmartBlocks

A **SmartBlock** should be a versioned, typed, policy-bound unit of work—not arbitrary code that can execute merely because it was stored.

Suggested record:
- `block_id`, `workspace_id`, `version`, `kind`, `input_schema`, `output_schema`
- `payload_ref` or content-addressed artifact reference
- `permissions`, `required_approvals`, `integrity_hash`
- `created_by`, `created_at`, `status`, `execution_record_id`

**Lifecycle:** draft -> validate schema -> scan/authorize -> approve if needed -> execute in a constrained runner -> capture outputs/logs -> verify -> publish or roll back.

Use ordinary transactional database semantics for the initial implementation. “Zero gas” is not a default property of a database or a consensus protocol: it can mean no per-transaction blockchain gas fee if no gas-metered chain is used, but hosting, storage, compute, networking, and validation still have costs. A decentralized, creator-owned validation network is a later research/implementation milestone, not an existing guarantee.

### Omni — orchestration

Omni should produce a structured run record:
- goal, plan steps, dependencies, and selected providers/tools
- permission checks and approval requirements
- each step's start/end time, status, inputs/outputs references, and error code
- evidence links, verification result, and final user-facing summary

**Execution state machine:** `draft -> planned -> awaiting_approval -> running -> verifying -> succeeded | failed | cancelled`.

Retries must be bounded and idempotent where possible. An agent task record is not itself a scheduler; background execution requires a real worker/queue, leases, retry policy, timeout, and observable job state.

### XParallel — interoperability and controlled execution

XParallel is the shared gateway and policy layer for connecting independent AI systems without requiring OneAI to own those systems. It should normalize capabilities, auth requirements, health, limits, and output evidence. Provider adapters remain optional; missing providers must yield explicit unavailable/skipped status rather than invented responses.

The existing execution approval gate remains authoritative. Never expose private execution routes directly to a public browser client.

### Parallel Verse — persistent world

The current development branch includes initial storage primitives for:
- agent registration
- named spaces
- append-only events
- task records
- SQLite by default and an opt-in PostgreSQL adapter

These are a useful foundation for world state, but task records do not yet prove a scheduler, live multi-agent runtime, autonomous evolution, or full identity-aware tenancy. The current shared bearer-token model and client-supplied workspace identifier must not be treated as secure public multi-tenant isolation.

### OneAI workspace

The UI should expose clear states for:
- Connected / unavailable / error / not yet verified
- Plan-only versus execution-enabled
- Awaiting approval and the exact requested action
- Evidence, logs, timestamps, and test results
- Workspace and agent identity context

Do not display raw backend URLs or secret-token entry fields as ordinary end-user controls. Keep configuration in server-side environment variables or a protected administrator setup flow.

## Persistence and $0 budget

- Keep SQLite for local development and tests.
- Do not use serverless `/tmp` as durable storage; data there can disappear between invocations or deployments.
- PostgreSQL remains opt-in and must fail closed if misconfigured.
- Do not provision paid database, model, hosting, or monitoring resources without explicit budget approval. The current authorized infrastructure budget is $0/month.
- Before claiming durable production memory, test save -> restart/new process -> retrieve, workspace separation, deletion/retention, and backup/restore against the actual deployed storage.

## Phased implementation plan

### Phase 0 — Preserve and inventory
- Keep the current Git history and existing route contracts.
- Treat `xparallel-parallel-verse-verify` and its PR as a development candidate; do not silently merge it into `main`.
- Map current modules and tests before adding duplicate abstractions.

### Phase 1 — Safe local foundation
- Review and run existing Parallel Verse and memory-vault tests.
- Keep SQLite defaults and add explicit test fixtures for workspace isolation.
- Define SmartBlock schemas and artifact metadata only; do not execute arbitrary stored payloads.
- Add architecture docs and a capability/status manifest.

### Phase 2 — Identity and tenancy
- Add a server-side principal-to-workspace binding.
- Enforce workspace membership on every Parallel Verse route and DB operation.
- Add auth denial, revocation, cross-workspace read/write, and audit tests.
- Replace shared bearer-token tenancy before any untrusted multi-user release.

### Phase 3 — Omni plan/evidence workflow
- Add a persisted run/step record and deterministic state transitions.
- Connect existing planner/router/provider adapters behind explicit capability checks.
- Add bounded timeouts, retries, idempotency, and human approval.
- Return verifiable execution evidence; no simulated success.

### Phase 4 — Jellybox SmartBlocks
- Implement schema validation, artifact hashing, versioning, permission manifests, and approval requirements.
- Run only in a constrained sandbox with resource/network limits.
- Add rollback and audit evidence.

### Phase 5 — Persistence and device trust
- Test durable storage with a disposable database before enabling it in a deployment.
- Implement backups and restore drills.
- Add platform-native device trust without collecting raw biometric information.

### Phase 6 — Parallel Verse runtime
- Introduce a real scheduler/worker only after task leases, retries, cancellation, and observability are designed.
- Add agent discovery and message/event subscriptions with workspace-scoped authorization.
- Evaluate versioned skills/configuration against tests before staged rollout.
- Treat blockchain/consensus and decentralized device nodes as separate research milestones.

## Release gates

Do not call the system production-ready until all relevant gates pass:
- CI and complete unit tests pass on the exact candidate commit.
- Real deployed health and system endpoints return expected statuses.
- Authentication, revocation, role enforcement, and cross-workspace isolation are verified.
- Memory survives restart/deployment using configured durable storage.
- At least one real configured model provider call is recorded with provider/model and error handling.
- Approval gates reject unauthorized execution; approved actions are bounded and audited.
- Backup/restore, rate limits, secrets handling, and mobile/browser flows are tested.
- No paid resource or production promotion occurs without explicit approval.

## Truthful status language

Use “implemented” only for code present on the reviewed branch; “automated tests pass” only for a recorded passing test run; “live verified” only for an observed real deployed response. Use “proposed” or “not yet verified” for architecture that has not met those standards.
