# AI Ecosystem Component Register

**Source:** owner-supplied “AI ecosystem — component brainstorm” (2026-11-02)  
**Branch:** `docs/113-component-register`  
**Purpose:** trace every source entry without silently dropping overlapping capabilities.  
**Evidence rule:** no item is declared implemented merely because its name appears in the brainstorm or a branch name. Repository/PR/code/tests must be inspected before changing status.

## Counting and reconciliation

Sections 1–10 contain **113 brainstorm entries**. Section 11 contains **15 existing identities to preserve**, tracked separately and excluded from the 113 count. Counting follows the source's component/capability bullets: the section 4 strategic interoperability ambition is not a separately named component; section 10's controlled-experiment capability and governed independent-agent network are counted as entries.

| Source section | Entries |
|---|---:|
| 1. Intelligence and cognition | 14 |
| 2. Omni knowledge | 13 |
| 3. Omni orchestration | 10 |
| 4. XParallel interoperability | 10 |
| 5. Creative intelligence | 14 |
| 6. Engineering/science/industrial | 10 |
| 7. Identity/trust/security | 11 |
| 8. Personal/organizational intelligence | 13 |
| 9. Infrastructure/computing | 12 |
| 10. Experimental | 6 |
| **Total** | **113** |
| Section 11 preservation identities (separate) | 15 |

## Status vocabulary

- **Unverified** — not yet inspected against repository code and tests (default status in this initial register).
- **Existing and verified** — implementation and relevant tests/evidence inspected.
- **Partial** — some, but not all, defined responsibility is implemented and verified.
- **Planned** — no verified implementation found; accepted for roadmap.
- **Experimental** — research/design candidate; not promised as production capability.
- **Blocked** — dependency, credentials, policy, hardware, or other documented blocker.

## Register: the 113 brainstorm entries

Columns: ID; source name; source responsibility / scope; proposed owner; dependencies and overlap notes; acceptance evidence; status.

### 1. Intelligence and cognition — 14 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C001 | Cognitive Core | Reasoning, analysis, problem-solving, decisions | ƎllE intelligence runtime | Model Gateway; Omni context | Task suite with traceable inputs/results | Unverified |
| C002 | Multi-Model Intelligence | Combine, compare, debate and synthesize models | Parallel Intelligence | Model Gateway; provider adapters | Multi-model run with attributed outputs | Unverified |
| C003 | Self-Evaluation Engine | Check answers, uncertainty and contradictions | Parallel Intelligence | Evaluation datasets; OmniTrace | Calibrated evaluation and contradiction tests | Unverified |
| C004 | Adaptive Intelligence | Improve workflows from approved feedback | ƎllE / Parallel Intelligence | Consent, versioning, rollback | Feedback opt-in, version history, rollback test | Unverified |
| C005 | Reasoning Laboratory | Test hypotheses, simulate scenarios, explore alternatives | Parallel Intelligence | C002, C006, sandbox/compute | Reproducible experiment record | Unverified |
| C006 | Decision Intelligence | Risk, forecasting, evidence-based recommendations | ƎllE domain capabilities | OmniSearch/Trace; uncertainty | Benchmark with evidence and uncertainty | Unverified |
| C007 | Context awareness engine | Use relevant session, project and environment context | ƎllE + Omni | OmniMemory; access controls | Context relevance and isolation tests | Unverified |
| C008 | Knowledge gap detector | Identify missing evidence or knowledge | Omni + ƎllE | OmniSearch; C003 | Known-gap benchmark and citations | Unverified |
| C009 | Explainability engine | Explain reasoning basis and evidence | ƎllE / Parallel Intelligence | OmniTrace; AROT | Explanation links to actual sources/artifacts | Unverified |
| C010 | Confidence and uncertainty evaluator | Estimate and communicate uncertainty | Parallel Intelligence | C003; evaluation data | Calibration metrics and abstention tests | Unverified |
| C011 | Scientific research assistant | Research synthesis and hypothesis support | ƎllE research capability | Omni connectors/search/trace | Source-backed research task | Unverified |
| C012 | Mathematical and engineering intelligence | Mathematics and engineering problem solving | ƎllE domain capabilities | QCode; Engineering Intelligence; verification | Unit-tested calculations and stated assumptions | Unverified |
| C013 | Strategic planning engine | Build plans against goals and constraints | OmniPlan + ƎllE | OmniFlow; OmniControl | Plan validation and approval flow | Unverified |
| C014 | Collective intelligence engine | Synthesize contributions from independent agents | Parallel Intelligence | XParallel; Agent Registry; trust policy | Attributed synthesis and disagreement record | Unverified |

### 2. Omni universal data and knowledge — 13 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C015 | OmniStream | Continuous authorized data ingestion | Omni knowledge plane | Connectors; consent; queues | Ingestion, retry and revoke tests | Unverified |
| C016 | OmniMemory | Persistent contextual/project memory | Omni knowledge plane | Storage Fabric; tenant isolation | Save/retrieve/delete/isolation tests | Unverified |
| C017 | OmniSearch | Unified search across connected sources | Omni knowledge plane | OmniIndex; OmniTrace; permissions | Relevant results with citations and ACL filtering | Unverified |
| C018 | OmniGraph | Relationships between entities, documents, events | Omni knowledge plane | Knowledge Genome; OmniTrace | Relationship query with provenance | Unverified |
| C019 | OmniVault | Protected knowledge/document storage | Omni + Storage Fabric | UIDaaS; encryption; retention | Access-control and lifecycle tests | Unverified |
| C020 | OmniIndex | Semantic, keyword and vector indexing | Omni knowledge plane | Storage; Vector Engine | Index/reindex/delete/search tests | Unverified |
| C021 | OmniSync | Synchronization and freshness management | Omni knowledge plane | OmniStream; connectors | Staleness and conflict tests | Unverified |
| C022 | OmniLens | Image/video/audio/document understanding | ƎllE multimodal + Omni | Model Gateway; file safety | Supported-format tests and truthful capability states | Unverified |
| C023 | OmniTrace | Information/source lineage | Omni knowledge plane | AROT; connectors; retrieval | Results resolve to source records | Unverified |
| C024 | OmniBridge | Knowledge exchange between AI systems | Omni + XParallel | Versioned contracts; permission policy | Authorized import/export contract test | Unverified |
| C025 | OmniArchive | Historical knowledge preservation | Omni + AROT | Storage Fabric; retention | Restore and historical retrieval tests | Unverified |
| C026 | OmniPulse | Monitor updates and emerging information | Omni knowledge plane | OmniStream/Sync; scheduler/events | Freshness alert with source evidence | Unverified |
| C027 | Knowledge Genome | Structured links among facts, evidence, concepts and discoveries | OmniGraph | OmniTrace; OmniIndex; AROT | Provenance-aware relationship traversal | Unverified |

### 3. Omni orchestration and autonomous work — 10 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C028 | OmniFlow | Visual workflow builder | Omni orchestration plane | OmniPlan; event/queue contracts | Create, run, pause and resume workflow tests | Unverified |
| C029 | OmniPlan | Convert objectives to executable plans | Omni orchestration plane | C013; OmniControl | Plan schema, constraints and approval tests | Unverified |
| C030 | OmniScheduler | Recurring and scheduled tasks | Omni orchestration plane | Queue/event bus; durable storage | Schedule, timezone and cancellation tests | Unverified |
| C031 | OmniSwarm | Coordinate specialized agent groups | Omni orchestration plane + Parallel Intelligence | Agent Registry; XParallel | Multi-agent coordination with audit | Unverified |
| C032 | OmniPilot | Supervise multi-step tasks | ƎllE + Omni orchestration | OmniFlow/Plan; status events | End-to-end task with checkpoints | Unverified |
| C033 | OmniControl | Permissions and approvals | UIDaaS / policy layer | Identity; audit; task contracts | Denied-by-default and approval tests | Unverified |
| C034 | OmniEvent | Event-driven automation | Shared event runtime | Event Bus; schema/versioning | Event delivery, deduplication and retry tests | Unverified |
| C035 | OmniSim | Simulate tasks before execution | Omni orchestration plane | Sandbox/Compute Fabric; World Model | Dry-run cannot cause external side effects | Unverified |
| C036 | OmniVerify | Verify execution results | Shared verification service | Task contracts; evidence; AROT | Result checks against explicit acceptance criteria | Unverified |
| C037 | OmniRecovery | Retry and recover failed operations | Shared reliability runtime | Queue Engine; durable state; idempotency | Fault injection and recovery tests | Unverified |

### 4. XParallel universal interoperability — 10 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C038 | XParallel Discovery | Discover compatible AI systems/services | XParallel | Registry; safe probes; egress policy | Authorized discovery and timeout tests | Unverified |
| C039 | XParallel Connect | Establish authorized connections | XParallel | UIDaaS; Credential Vault; connector SDK | Auth, revoke and reconnect tests | Unverified |
| C040 | XParallel Roaming | Workers operate in approved environments | XParallel roaming runtime | Registry; queues; sandbox; policy | Register/heartbeat/task/result/revoke lifecycle | Unverified |
| C041 | XParallel Exchange | Standardized information/task exchange | XParallel | Protocol; versioned contracts | Contract compatibility tests | Unverified |
| C042 | XParallel Protocol | Common communication contracts | XParallel | Auth; versioning; schema validation | Compatibility and invalid-payload tests | Unverified |
| C043 | XParallel Mesh | Distributed network of workers/systems | XParallel | C038–C042; observability | Node failure and isolation tests | Unverified |
| C044 | XParallel Sandbox | Isolated execution environments | XParallel + Compute Fabric | Least privilege; egress restrictions | Escape/egress and resource-limit tests | Unverified |
| C045 | XParallel Registry | Discoverable agent/service directory | XParallel | UIDaaS; manifests; health | Registration, lookup, stale entry and revoke tests | Unverified |
| C046 | XParallel Passport | Portable, revocable agent identity | UIDaaS + XParallel | Signed claims; expiry; revocation | Signature, scope, expiry and revoke tests | Unverified |
| C047 | Parallel Verse | Persistent environment for agents to coexist and collaborate | XParallel | Registry; events; storage; sandbox | Persistence, tenant isolation and recovery tests | Unverified |

### 5. Creative intelligence — 14 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C048 | Image Studio | Image creation workflow | Build Studio | Model Gateway; media adapters | Generation/edit path and provider-status tests | Unverified |
| C049 | Video Studio | Video creation workflow | Build Studio | Media adapters; storage/compute | Supported workflow with artifact verification | Unverified |
| C050 | Audio and Music Studio | Audio/music creation workflow | Build Studio | Audio adapters; rights/consent | Artifact playback and provenance tests | Unverified |
| C051 | Build Studio | Unified creation/development workspace | Build Studio | QCode; media tools; sandbox | Create-preview-test workflow | Unverified |
| C052 | Website and application generator | Generate websites/apps | Build Studio + QCode | Templates; sandbox; verification | Build/test/preview against requirements | Unverified |
| C053 | Game development assistant | Game development support | Build Studio + QCode | Asset pipeline; sandbox | Example project build and tests | Unverified |
| C054 | 3D modeling and design | 3D model/design workflows | Build Studio | Supported 3D formats; compute | Export/import validity checks | Unverified |
| C055 | CAD and engineering design | CAD workflows | Engineering Intelligence + Build Studio | CAD formats; engineering verification | File validity and engineering review gates | Unverified |
| C056 | Presentation and document studio | Create presentations/documents | Build Studio | Omni knowledge; export/render tools | Rendering and citation tests | Unverified |
| C057 | Voice cloning with consent safeguards | Consent-based voice cloning | Audio and Music Studio | Explicit consent; provider policy; rights | Consent, revoke and output disclosure tests | Unverified |
| C058 | Animation and character creation | Animation/character workflows | Build Studio | 3D/media adapters | Valid artifact export and preview | Unverified |
| C059 | Digital twin builder | Build digital-twin representations | Engineering Intelligence | OmniGraph; simulation/compute | Model schema and validation tests | Unverified |
| C060 | Interactive simulation studio | Interactive simulation workflows | Build Studio + Engineering Intelligence | Compute; Sandbox; World Model | Reproducible simulation run | Unverified |
| C061 | Brand and marketing studio | Brand/marketing asset workflows | Build Studio | Image/document studio; policy | Asset export and user review | Unverified |

### 6. Engineering, science and industrial intelligence — 10 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C062 | Engineering AI | Mechanical, electrical, civil and chemical engineering | ƎllE Engineering Intelligence | Omni knowledge; QCode; verification | Domain benchmark and assumptions reporting | Unverified |
| C063 | Thermal Intelligence | Thermodynamics, heat transfer, energy systems | ƎllE Engineering Intelligence | C012/C062; unit-aware compute | Reference-case calculation tests | Unverified |
| C064 | Industrial AI | Equipment monitoring and maintenance | Engineering Intelligence | Data Fabric; telemetry; permissions | Simulated telemetry and alert tests | Unverified |
| C065 | Digital Twin Intelligence | Virtual models of physical assets | Engineering Intelligence | C059; OmniGraph; World Model | Model synchronization and validation tests | Unverified |
| C066 | Predictive Maintenance | Identify likely equipment failures | Engineering Intelligence | C064; historical data; evaluation | Held-out data evaluation with uncertainty | Unverified |
| C067 | Scientific Discovery | Research, experiments, hypothesis generation | ƎllE research capability | OmniTrace; Reasoning Lab; experiment controls | Reproducible, source-linked research record | Unverified |
| C068 | Robotics Intelligence | Connect to supported robotics systems | Engineering Intelligence + XParallel | Device permissions; safety sandbox | Simulation-first, safe command authorization | Unverified |
| C069 | Geospatial Intelligence | Mapping, remote sensing, spatial analysis | Engineering Intelligence | Geospatial connectors; OmniLens | Coordinate/format validation and provenance | Unverified |
| C070 | Energy Intelligence | Optimize generation, storage and consumption | Engineering Intelligence | C063/C065; telemetry; constraints | Constrained simulation and benchmark | Unverified |
| C071 | Agricultural Intelligence | Crop, soil, weather and livestock support | Engineering Intelligence | Geospatial/data connectors; OmniTrace | Source-backed recommendations and limitations | Unverified |

### 7. Identity, trust and security — 11 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C072 | UIDaaS | Universal digital identity and access | UIDaaS | Authentication; authorization; tenant model | AuthZ, session and tenant isolation tests | Unverified |
| C073 | AI Guardian | Security monitoring and threat detection | Shared security/observability | Logs; policy; incident workflow | Simulated threat and alert tests | Unverified |
| C074 | Trust Engine | Assess source/provider trust | Shared trust services | Provenance; source metadata; policies | Explainable trust score with evidence | Unverified |
| C075 | Permission Engine | Granular authorization | UIDaaS / policy layer | Identity; resource scopes | Deny-by-default matrix tests | Unverified |
| C076 | Privacy Vault | Protected personal information | UIDaaS + Storage Fabric | Encryption; consent; retention | Access, export and deletion tests | Unverified |
| C077 | Credential Vault | Server-side secret management | Shared security infrastructure | Runtime config; rotation; redaction | Secret never reaches browser/log/source | Unverified |
| C078 | AROT | Historical evidence and integrity | AROT provenance service | Hashes; immutable history where feasible | Tamper detection and chain-of-custody tests | Unverified |
| C079 | VOUCHER | Attribution and verification mechanisms | VOUCHER | AROT; identity; evidence rules | Attribution trail; no unsupported ownership claims | Unverified |
| C080 | AI Firewall | Inspect/control inbound and outbound AI operations | Shared security infrastructure | Policy; egress controls; tool registry | Allow/deny, prompt-injection and egress tests | Unverified |
| C081 | Policy Engine | Enforce platform/workspace rules | Shared policy layer | UIDaaS; OmniControl; audit | Policy decision and enforcement tests | Unverified |
| C082 | Audit Intelligence | Explain who/what acted and why | AROT + observability | Auth identity; policy decision; event records | Reconstructable action timeline | Unverified |

### 8. Personal and organizational intelligence — 13 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C083 | Business intelligence assistant | Business analysis and decision support | ƎllE domain capability packs | OmniSearch; provenance; access controls | Reproducible report with source citations | Unverified |
| C084 | Enterprise knowledge assistant | Organization-scoped knowledge access | ƎllE + Omni | UIDaaS; tenant-isolated Omni | Cross-tenant leakage tests | Unverified |
| C085 | Digital secretary | Administrative task assistance | ƎllE + OmniFlow | Calendar/mail connectors; approvals | Explicitly approved actions and audit | Unverified |
| C086 | Personal research librarian | Organize and retrieve personal research | Omni + ƎllE | OmniMemory/Search/Archive; consent | Citation, source import/export and deletion tests | Unverified |
| C087 | Project manager AI | Project planning and status support | ƎllE + OmniFlow | OmniPlan; events; workspace controls | Task-state consistency and approval tests | Unverified |
| C088 | Financial analysis assistant | Financial analysis and scenarios | ƎllE domain capability packs | Data validation; uncertainty; privacy | Calculation tests and clear non-advice boundaries | Unverified |
| C089 | Education and tutoring intelligence | Learning and tutoring support | ƎllE domain capability packs | User preferences; content provenance | Learning-task evaluation and age safeguards | Unverified |
| C090 | Legal research assistant with jurisdiction controls | Jurisdiction-aware legal research | ƎllE domain capability packs | Source freshness; jurisdiction metadata | Jurisdiction/source checks and disclaimers | Unverified |
| C091 | Medical information assistant with clinical safeguards | Safeguarded medical information | ƎllE domain capability packs | Trusted sources; clinical safety controls | Safety evaluation and escalation tests | Unverified |
| C092 | Customer service agent | Customer support workflows | UnitAI + ƎllE | Knowledge base; identity; approval policies | Grounded response and escalation tests | Unverified |
| C093 | Team collaboration intelligence | Team knowledge and coordination | ƎllE + Omni | Workspace permissions; event bus | Membership and isolation tests | Unverified |
| C094 | Personal knowledge graph | Personal entity/relationship graph | OmniGraph | OmniMemory; privacy permissions | User-scoped graph and deletion tests | Unverified |
| C095 | Multi-user collaborative workspaces | Shared workspace and collaboration | OneAI workspace + UIDaaS | Membership; roles; audit | Invite/revoke and tenant isolation tests | Unverified |

### 9. Infrastructure and computing — 12 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C096 | Compute Fabric | Access local and cloud computing | Shared platform infrastructure | Policy; sandbox; resource quotas | Local profile and quota tests | Unverified |
| C097 | Model Gateway | Standardized model access | Shared model runtime | Adapter registry; secrets; policy | Provider contract suite; safe fallback | Unverified |
| C098 | Data Fabric | Unified data connectivity | Omni + connector infrastructure | Connector SDK; permissions | Connector contract and ACL tests | Unverified |
| C099 | Storage Fabric | Files, objects and databases | Shared platform infrastructure | Storage adapters; migrations; backups | Persistence, isolation and restore tests | Unverified |
| C100 | Vector Engine | Semantic retrieval | Omni knowledge plane | Embeddings; OmniIndex; permissions | Retrieval benchmark and deletion propagation | Unverified |
| C101 | Event Bus | Internal communication | Shared runtime | Versioned event schemas | Delivery, ordering and duplicate handling tests | Unverified |
| C102 | Queue Engine | Reliable task delivery | Shared runtime | Event Bus; durable state; idempotency | Retry/dead-letter/replay tests | Unverified |
| C103 | API Gateway | External and internal APIs | Shared platform infrastructure | UIDaaS; rate limits; versioned contracts | Auth, validation, throttling and contract tests | Unverified |
| C104 | Edge Runtime | Local and distributed inference | Shared runtime / XParallel | Model Gateway; hardware capability detection | Offline/local inference smoke test | Unverified |
| C105 | Observability Engine | Logs, metrics and traces | Shared platform infrastructure | Redaction; event model; alerting | Correlated trace and secret-redaction tests | Unverified |
| C106 | Backup Engine | Recovery and continuity | Shared platform infrastructure | Storage Fabric; AROT; runbooks | Automated backup and restore drill | Unverified |
| C107 | Developer SDK | Third-party integration | Shared developer platform | API Gateway; contracts; auth docs | Example integration and compatibility tests | Unverified |

### 10. Experimental components — 6 entries

| ID | Source name | Responsibility | Proposed owner | Dependencies / overlap | Acceptance evidence | Status |
|---|---|---|---|---|---|---|
| C108 | Parallel Reality Engine | Compare multiple possible solutions/scenarios | Parallel Intelligence research | C005; World Model; sandbox | Reproducible scenario comparison | Experimental |
| C109 | Controlled experiments for agent workflows | Improve workflows/prompts/capabilities with versioning and rollback | Parallel Intelligence research | Evaluation; version store; approval | Experiment isolation, rollback and audit tests | Experimental |
| C110 | Time Intelligence | Connect historical records, present information and forecasts | Omni + Parallel Intelligence | OmniArchive/Trace; forecasting evaluation | Time-aware provenance and forecast evaluation | Experimental |
| C111 | Governed network of independent AI agents | Share discoveries and specialist knowledge | XParallel + Parallel Intelligence | C045/C046; trust and policy | Consent, provenance, isolation and revocation tests | Experimental |
| C112 | World Model | Structured environment/system/object model for simulation/planning | OmniGraph + Engineering Intelligence | Knowledge Genome; compute/simulation | Model consistency and simulation tests | Experimental |
| C113 | Universal AI Passport | Portable agent identity, permissions and capability declarations | UIDaaS + XParallel | C046; signed claims; revocation | Cross-system validation, scope and revoke tests | Experimental |

## Section 11: existing identities to preserve (15, tracked separately)

These are preservation targets, not additional entries in the 113 count. Their status must be determined from code and tests.

| ID | Existing identity | Intended responsibility | Proposed owner / boundary | Evidence needed | Status |
|---|---|---|---|---|---|
| P001 | ƎllE | Primary intelligence interface | User-facing intelligence runtime | Real provider/local inference, persistence, diagnostics | Unverified |
| P002 | Omni | Knowledge stream and orchestration identity | Separate knowledge and orchestration planes | Separate contracts and no duplicated responsibility | Unverified |
| P003 | XParallel | Interoperability and roaming | Cross-system task transport/execution | Worker lifecycle and protocol tests | Unverified |
| P004 | Parallel Intelligence | Collaborative cognition | Multi-model/agent coordination | Attributed comparison and synthesis tests | Unverified |
| P005 | AROT | Historical evidence and accountability | Provenance and integrity | Artifact lineage, integrity and recovery tests | Unverified |
| P006 | UnitAI | Specialized AI units and agents | Agent types/specialist capabilities | Manifests, permissions and lifecycle tests | Unverified |
| P007 | Omnibox | Universal command and access | Unified command/access surface | Route/command authorization tests | Unverified |
| P008 | Jellybox | Consent-based data collection and exchange | Consent/data exchange capability | Consent, scope, revoke and audit tests | Unverified |
| P009 | QCode | Coding and developer intelligence | Developer tooling | Repository/test workflow and sandbox tests | Unverified |
| P010 | UIDaaS | Identity and access | Identity/authN/authZ | Session, resource authorization and isolation tests | Unverified |
| P011 | VOUCHER | Attribution and verification | Attribution mechanisms | Evidence chain and clear legal limitations | Unverified |
| P012 | WFAIAI OS | Workflow and operating environment | Reuse OmniFlow where overlapping | Existing contracts and workflow tests | Unverified |
| P013 | Build Studio | Creation and development | Umbrella creation workspace | Create/build/test/preview tests | Unverified |
| P014 | AI Repair Shop | Diagnostics and repair | Repair proposal and approval workflow | Diagnose, propose, test, approve and rollback | Unverified |
| P015 | AI Mixer | Multi-model routing and comparison surface | User-facing model selection/collaboration UI | Provider selection, attribution, fallback and tests | Unverified |

## Explicit overlap rules

1. OmniStream ingests; OmniMemory stores contextual memory; OmniGraph models relationships; OmniIndex indexes; OmniSearch retrieves; OmniTrace links results to sources; OmniArchive preserves history. Knowledge Genome organizes relationships across these. These are distinct responsibilities, even if code is shared.
2. OmniFlow/OmniPlan/OmniScheduler/OmniSwarm/OmniPilot/OmniControl/OmniEvent/OmniSim/OmniVerify/OmniRecovery are orchestration capabilities, not the knowledge stream.
3. Model Gateway is provider-neutral backend access. AI Mixer is the user-facing selection/comparison experience. Parallel Intelligence coordinates collaborative reasoning.
4. Agent Registry catalogs identities/capabilities; XParallel transports authorized tasks; roaming workers execute within policy; Parallel Verse is the persistent agent environment.
5. UIDaaS owns identity and access. XParallel Passport and Universal AI Passport are overlapping credential concepts: retain both source names as separately traceable entries, but evaluate a shared portable-credential implementation rather than duplicating identity systems.
6. OmniVerify validates artifacts/results; Self-Evaluation evaluates answer/reasoning quality; AROT records provenance/integrity/history. Share evidence infrastructure but preserve distinct acceptance tests.
7. Compute Fabric provides compute; XParallel Sandbox constrains execution; Storage Fabric persists data; Event Bus/Queue Engine transport events/tasks; Observability diagnoses; Backup Engine restores.
8. Build Studio is the creation umbrella; Image/Video/Audio and Music studios are focused workflows; QCode is developer capability; AI Repair Shop handles diagnose/propose/test/approval/rollback.
9. Existing identities remain discoverable even if their implementation is shared with another subsystem. Shared implementation is not omission.

## Dependency-first delivery phases

- **A — Audit and traceability:** inspect main, relevant branches, open/closed PRs, routes, schemas, configuration, tests and deployment files; assign evidence-backed status to every C001–C113 and P001–P015.
- **B — Security/runtime foundation:** UIDaaS, Permission/Policy Engine, Credential Vault, API Gateway, Model Gateway, Storage Fabric, Event Bus, Queue Engine, Observability and AROT contracts.
- **C — Omni knowledge plane:** authorized connectors/OmniStream → normalize/index/store → OmniMemory/Graph/Genome → OmniSearch → OmniTrace/Archive/Sync/Pulse.
- **D — Intelligence:** ƎllE/Cognitive Core + Model Gateway + Omni context; Multi-Model Intelligence/Parallel Intelligence; Self-Evaluation, explainability and OmniVerify with distinct tests.
- **E — Orchestration and interoperability:** OmniFlow/Plan/Scheduler/Control/Event/Recovery; Agent Registry; XParallel Protocol/Connect/Discovery/Exchange/Roaming/Mesh/Sandbox; then Parallel Verse and portable passport contract.
- **F — Creation and domain capabilities:** Build Studio, QCode, media studios, repair, engineering/science/industrial and organizational capability packs.
- **G — Experimental and hardening:** experiments, World Model, Parallel Reality, Time Intelligence; security review, restore drills, mobile/low-bandwidth behavior, docs and release evidence.

## Repository audit checklist

For every entry, record: inspected branches/PRs and paths; relevant commits; whether functionality is actually called by the app; tests run and outcomes; runtime/live evidence; security/tenant boundaries; known blockers; proposed next change. Branch names, issue text, screenshots and green builds alone do not establish working functionality.

## Safety and release gates

- Keep changes on dedicated development branches and use reviewable commits.
- Preserve history, working routes and existing integrations; do not create a replacement starter project.
- Secrets stay server-side; all operations are permission-scoped and audited.
- Default to local-first/open-source and $0/month-compatible choices; optional paid integrations must be opt-in.
- No production deployment, default-branch merge, paid resource activation, token issuance, or irreversible external action without explicit owner approval.
- Do not mark the register complete until every C001–C113 and P001–P015 has a source-to-code/test evidence record or an explicit planned/experimental/blocked status.
