# XParallel Capability Verification Laboratory — Draft 0.1

## Objective

Move capability status from self-declared claims to evidence-backed test outcomes. The lab binds each run to an exact entity, capability version, immutable artifact SHA-256 digest, trusted test-plan version, verifier subject, per-case evidence references, and expiry.

## Evidence states

- `unverified`: no successful current evidence, or artifact digest changed.
- `verified`: every required case in the trusted plan passed, evidence references were returned, and the verification has not expired.
- `failed`: at least one required case failed.
- `inconclusive`: at least one required case was blocked and none failed.
- `expired`: the most recent successful run has passed its expiry.
- `suspended`: a separately authorized verifier/governance actor suspended this capability version.
- `revoked`: a separately authorized actor revoked this capability version. Revocation is terminal for that version.

A later run replaces the previous outcome for the same capability version and exact artifact digest, except that a revoked version cannot be rerun. A new artifact digest or capability version requires fresh evidence.

## Trust boundaries

Four host adapters are mandatory:
- `authenticate(session)`: returns trusted authenticated subject and workspace.
- `authorize_verifier(principal, entity, capability, operation)`: checks verifier authority for run, read, audit, suspend, or revoke.
- `resolve_test_plan(plan_id, version, entity, capability)`: returns the trusted test case identifiers for the exact entity/capability.
- `execute_tests(...)`: invokes an isolated test runner against the exact artifact and returns case outcomes and evidence references.

The lab does not execute arbitrary test code or accept a caller-supplied result as trusted. The test-plan resolver and runner are trusted infrastructure and must be independently secured. A malicious or incorrectly sandboxed adapter can falsify results; this prototype cannot prove sandbox isolation.

## Verification run

1. Authenticate the verifier and check per-entity/capability authority.
2. Validate entity/capability identifiers, semantic version, artifact digest, plan identity and bounded expiry.
3. Resolve the trusted test plan; reject plan identity/version mismatches, duplicate cases, empty plans and oversized plans.
4. Invoke the injected isolated runner.
5. Require exactly one result for every required case; reject unexpected, duplicate, incomplete or evidence-free results.
6. Classify the run: all pass = passed; any fail = failed; otherwise blocked = inconclusive.
7. Store append-only run evidence and a digest of normalized per-case outcomes.
8. Expose a derived status only when the artifact digest and capability version match and evidence remains current.

## Safety and integrity properties

- Workspace-scoped SQLite records and queries.
- No private credentials or executable test code stored by this module.
- Artifact identity is pinned to a SHA-256 digest.
- Verification plan and case IDs are resolved by a trusted adapter.
- Every required test must return an evidence reference.
- Expiry is bounded to 30 days.
- Suspension and revocation require verifier authority and a reason.
- Revocation is terminal for that capability version.
- Verification runs and state changes have append-only event records through this API.

## Limitations

- This is a local SQLite prototype; a privileged database operator can alter records.
- Evidence references are pointers, not proof that external evidence storage is immutable or available.
- The sandbox is injected and not implemented here; do not run hostile code until a separately hardened isolation service is supplied.
- No API routes or production runtime are changed.
- The existing authorization policy still receives a trusted capability status from its caller. Production integration must derive that status from this lab for the exact artifact/version and fail closed if the lab is unavailable.
- A passing test suite proves only the tested behavior under the recorded environment; it does not prove general intelligence, consciousness, safety in every context, or unrestricted competence.
- No automatic update of the Digital DNA manifest to `verified` occurs. The manifest remains a declaration; verification is a separate evidence record.

## Production acceptance requirements

Use a hardened, ephemeral sandbox with CPU/memory/time/network quotas, read-only artifact mounts, no ambient credentials, syscall/container isolation, deterministic plan registry, signed artifact provenance, external append-only evidence storage, real verifier identity and role administration, tamper-evident audit, concurrency controls, rate limits, and independent security review. Wire the derived status into the action authorization boundary only after these controls exist.

## Status

Prototype and unit tests only. No production API integration, runtime enforcement, deployment, or paid service.
