# XParallel Interoperability Evidence Audit

Date: 2026-11-15
Repository inspected: `axali-sys/Unity-AI-Voice-Interface`
Source baseline inspected: `main` at `142f6ac02c9991229ff5f1054364ce02835804b1`
Documentation branch: `oneaiplus/unification-foundation-2026-11-14`

## Scope and evidence standard

This is a static source-and-test inventory, not a live deployment certification. The source files and test files below exist on the inspected main baseline. Test definitions were inspected; this audit did not execute the test suite. The successful GitHub Actions runs visible for the documentation branch are not proof that these runtime modules were tested by those docs-only commits.

## Component evidence

| Register ID | Component | Source evidence | Test evidence | Status and boundary |
|---|---|---|---|---|
| C038 | XParallel Discovery | `xparallel/entity_federation.py` | `tests/test_entity_federation.py` | Partial: signed public-record discovery, allowlist, owner binding and rate-limit cases exist. Live network discovery and operational registry availability are not certified. |
| C039 | XParallel Connect | `xparallel/entity_governance.py`, `xparallel/entity_authorization.py`, `xparallel/secure_transport.py` | `tests/test_entity_governance.py`, `tests/test_entity_authorization.py`, `tests/test_secure_transport.py` | Partial: grant request/approval/revoke and authorization primitives exist. Production credential provisioning and real peer connection lifecycle are not certified. |
| C040 | XParallel Roaming | `xparallel/roaming_ai.py`, `xparallel/parallel_world.py` | `tests/test_roaming_ai.py`, `tests/test_parallel_world.py` | Partial: opt-in planner/researcher/arbiter proposal pipeline; bounded context, response hashes and explicit no-execution result. Depends on configured AI provider and memory. It does not prove autonomous roaming workers or external execution. |
| C041 | XParallel Exchange | `xparallel/entity_messaging.py`, `xparallel/protocol_compat.py` | `tests/test_entity_messaging.py`, `tests/test_protocol_conformance.py` | Partial: message/protocol primitives exist. Live cross-organization exchange and peer interoperability are not certified. |
| C042 | XParallel Protocol | `xparallel/protocol_compat.py`, `xparallel/manifest.json` | `tests/test_protocol_conformance.py` | Partial: compatibility/conformance surface exists. Version negotiation against independently operated peers is not certified. |
| C043 | XParallel Mesh | `xparallel/entity_federation.py`, `xparallel/entity_messaging.py` | `tests/test_entity_federation.py`, `tests/test_entity_messaging.py` | Planned/partial foundation: federation and messaging primitives are not evidence of a resilient distributed mesh, routing, failover or node health network. |
| C044 | XParallel Sandbox | `xparallel/docker_runner.py`, `xparallel/docker_cgroup_meter.py`, `xparallel/execution_worker.py` | `tests/test_docker_cgroup_meter.py`, `tests/test_execution_worker.py`, `tests/test_trusted_execution.py` | Partial: controlled worker/runner and resource-measurement code exist. Container availability, isolation/escape resistance, egress restrictions and production host hardening require runtime verification. |
| C045 | XParallel Registry | `xparallel/entity_governance.py`, `xparallel/entity_federation.py`, `xparallel/parallel_verse.py` | `tests/test_entity_governance.py`, `tests/test_entity_federation.py`, `tests/test_parallel_verse.py` | Partial: governance grants, public discovery records and capability-based agent lookup exist in distinct modules. A single deployed, durable, federated registry is not certified. |
| C046 | XParallel Passport | `xparallel/identity_trust.py`, `xparallel/entity_federation.py`, `xparallel/session_jwt.py` | `tests/test_identity_trust.py`, `tests/test_entity_federation.py`, `tests/test_session_jwt.py` | Partial: signed identity/trust and host-session verification primitives exist. Portable cross-system passport issuance, key rotation, trust federation and revocation at all peers are not certified. |
| C047 | Parallel Verse | `xparallel/parallel_verse.py`, `xparallel/parallel_verse_service.py` | `tests/test_parallel_verse.py`, `tests/test_parallel_verse_service.py` | Partial: persistent agent/space/task/event primitives and workspace-isolation tests are present. Multi-node persistence, recovery under failure and live multi-agent operation are not certified. |

## Additional verified source boundaries

- `xparallel/entity_governance.py` documents trusted server-side authentication, ownership and governance adapters; its registry is SQLite-backed and deny-by-default.
- `xparallel/server.py` keeps execution and entity-governance adapters inert until explicit host bootstrap. Governance routes fail closed if JWT identity or trusted adapters are unavailable.
- `xparallel/execution_http_api.py` requires the host services and control plane to share the same approval registry; execution is not automatically activated by importing the module.
- `xparallel/session_jwt.py` verifies host-issued HS256 JWTs; it does not issue identities or authenticate users itself.
- `xparallel/http_identity.py` derives actor/workspace identity from verified claims and rejects caller overrides.
- `xparallel/roaming_ai.py` runs planner → read-only evidence gatherer → arbiter and returns `execution.performed=false`; it is a proposal pipeline, not a general-purpose autonomous executor.
- `xparallel/parallel_verse.py` has explicit tests for persistence across database reopen, workspace isolation, capability discovery, invalid inputs and cross-workspace reference rejection.

| C045 | XParallel Registry | `xparallel/parallel_verse.py` | `tests/test_parallel_verse.py` | Partial: workspace-scoped agent registration, capability lookup, persistence across database reopen and cross-workspace reference rejection. This is a local registry primitive, not a deployed federated service registry. |
| C082 | Audit Intelligence | `xparallel/audit_repository.py` | `tests/test_audit_repository.py` | Partial: workspace-filtered actor/action event storage and a single-event round-trip test. No complete action timeline, identity/policy correlation, tamper-evident chain or production durability is certified. |

## Additional component boundary review — 2026-11-15

The following adjacent modules were inspected to avoid promoting components based on name similarity alone:

- **C003 Self-Evaluation Engine — remains Unverified:** `xparallel/cognitive_runtime.py` includes an `evaluate_cases` harness and structured-output validation. The inspected tests check exact expected values and schema errors; they do not establish calibrated confidence, contradiction detection, reasoning-quality scoring, or a validated self-correction loop.
- **C005 Reasoning Laboratory — remains Unverified:** `xparallel/experiment.py` and `xparallel/simulator.py` create an experiment record and deterministic simulation result. The simulator explicitly does not execute arbitrary code and states that simulation success is not production proof. No inspected test suite establishes reproducible scientific experiment management, hypothesis comparison, or validated scenario modelling.
- **C017 OmniSearch — remains Unverified:** no dedicated OmniSearch implementation or ACL-filtered cross-source retrieval test was identified in the inspected `xparallel/` module and `tests/` inventories. The simple text search in `xparallel/graph.py` is not a unified, permission-aware source search service.
- **C018 OmniGraph / C027 Knowledge Genome — remain Unverified:** `xparallel/graph.py` is an in-memory Solution Graph for solution records, with keyword matching and candidate-to-verified status promotion. Its tests cover add/search/promote and fingerprint changes. It is not a persistent entity/document/event relationship graph with provenance-aware traversal, so it is not counted as OmniGraph or Knowledge Genome delivery.
- **C015 OmniStream and C023 OmniTrace — remain Unverified:** the inspected connector helper fetches a caller-supplied HTTPS URL with a byte limit, but no ingestion queue, consent/revocation lifecycle, source-lineage graph, or retrieval-to-source resolution test was identified. A connector fetch alone does not establish continuous ingestion or lineage.
- **C036 OmniVerify — remains Unverified:** structured-output schema validation and execution receipt verification are narrower controls. No general acceptance-criteria verifier for arbitrary workflow results was identified in this review.

These are scoped repository inspections, not proof that no related code exists anywhere in the wider ecosystem. The register remains conservative: no status promotion is made from a similarly named but materially narrower primitive.

| C037 | OmniRecovery | `xparallel/execution_recovery_service.py`, `xparallel/execution_recovery_supervisor.py`, `xparallel/execution_recovery_health_store.py` | `tests/test_execution_recovery_service.py`, `tests/test_execution_recovery_supervisor.py`, health-store tests | Partial: bounded recovery of already-persisted execution finalizations, fresh executor session, single-flight cycle, disabled-by-default explicit supervisor, optional append-only secret-free health history. Not general workflow retry or fleet scheduler; no live host recovery drill certified. |

## Operational gaps still open

1. Execute the full targeted test suite against a reproducible checkout and record exact command, environment, test count and result.
2. Verify configured JWT issuer/audience/secret, trusted host authentication, owner resolution and governance adapters in a non-production environment.
3. Verify XParallel public routes and authenticated private routes against the actual Render service, including allowed origins and expected failure cases.
4. Verify SQLite path durability and backup/restore semantics on the actual hosting platform; do not infer durable persistence from local SQLite tests.
5. Run sandbox resource, network-egress and isolation tests on a controlled host before enabling execution.
6. Test real peer-to-peer discovery, protocol negotiation, message exchange, key rotation and revocation across independent deployments.
7. Keep all execution behind explicit approval and the XParallel authorization boundary. Revocation remains an XParallel authorization control; it must not interfere with ordinary Oneaiplus chat.

## Release conclusion

No component in this audit is promoted to fully operational based on static inspection alone. The listed modules and test cases establish implementation foundations and test intent. Runtime, host configuration, peer interoperability, sandbox isolation and deployment evidence remain required. No production deployment, main merge or external execution was performed for this audit.

## CI execution update — 2026-11-15

The earlier static-audit statement above describes the audit's original inspection point. Subsequent isolated-branch commits expanded the GitHub Actions workflow to run the selected authorization, identity, execution-route, JWT-binding and governance suites. The latest recorded successful run at commit `84c72ead9c1868690eb4b7fba6d2774cd367e783` completed both workflows:

- [XParallel Integration Tests (DRI-001)](https://github.com/axali-sys/Unity-AI-Voice-Interface/actions/runs/43682039561) — success.
- [Verify Axaliai V1](https://github.com/axali-sys/Unity-AI-Voice-Interface/actions/runs/43682039544) — success.

The XParallel workflow includes `tests/test_execution_http_transport.py`, which starts a temporary loopback HTTP server and sends actual HTTP requests through the request handler. It verifies that the private health route rejects a missing bearer token and that an authenticated intent request passes verified claims and the original session token to a test-double execution API.

**Limit:** these are CI tests with a test verifier and test execution adapter. They do not validate the production JWT issuer/audience/secret, Render environment variables, actual host adapters, public-origin allowlist, real peer interoperability, or sandbox isolation. The XParallel component statuses remain Partial, not operational.
