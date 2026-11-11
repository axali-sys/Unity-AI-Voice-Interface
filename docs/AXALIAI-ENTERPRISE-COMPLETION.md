# AXALIAI Enterprise Completion — Development Execution Baseline

## Authorization and safety boundary

Owner authorization dated 2026-11-11 permits development of all enterprise milestones on isolated development branches only. The authorization explicitly prohibits:
- merging into `main` or `master`;
- production deployments or production configuration changes;
- paid services, purchases, or paid resource commitments;
- changing or absorbing the identities, repositories, or histories of existing products.

NexAI and IDEAS remain independent. ƎllE, XParallel, Omni, Parallel Intelligence, UnitAI and the other existing product identities retain their documented boundaries.

## Repository baseline

Primary integration repository: `axali-sys/Unity-AI-Voice-Interface`.
Integration branch: `enterprise/axaliai-completion`.
Base: existing `feat/elle-omni-knowledge-genome` branch, which contains the ƎllE/Omni foundation from draft PR #59. This is a development branch; it is not a merge into the default branch.

Existing work to preserve and reconcile:
- PR #59: ƎllE lifecycle, Omni knowledge genome, Parallel Intelligence, XParallel dispatch and AROT evidence.
- PR #58: traceable 113-component register and 15 separately tracked preservation identities.
- PR #60: Axaliai enterprise website and explicit preview/release gates.
- Previously merged XParallel registry, task queue, roaming worker, security, persistence and enterprise foundations.

These branches/PRs are not assumed to be production-ready or automatically combined. Their code and test evidence must be reconciled before integration.

## First security slice: trusted tenant identity

`xparallel/tenant_identity.py` adds short-lived HS256 identity claims for use by a future trusted login adapter. It is intentionally separate from `XP_TOKEN`, which is a service credential and not a human identity.

The issuer function is server-side only. It must be called only after a real authentication provider has authenticated the human and resolved their organization/workspace membership. Browser-supplied actor, role or workspace claims must never be signed.

Configuration:
- `XP_IDENTITY_SIGNING_SECRET`: random secret of at least 32 bytes, configured only in a server-side development environment.
- Identity tokens expire within 15 minutes by default and at most one hour.
- Supported roles: owner, admin, operator, viewer.

This first slice is a tested token primitive, not a complete login system. It is not yet wired into HTTP route authorization. Until route adapters enforce these claims and validate workspace membership, the new enterprise APIs must not be exposed as multi-tenant user APIs.

## Milestone sequence and gates

1. Repository reconciliation and identity boundary.
2. Authenticated organization/workspace membership and route enforcement.
3. Omni memory/retrieval/knowledge integration, with provenance, deletion and backup/restore.
4. ƎllE lifecycle and Parallel Intelligence provider abstraction, with honest unavailable states.
5. XParallel registry, roaming task lifecycle, least-privilege sandbox and execution approval.
6. Product adapters and mobile-first command center; preserve independent product identity.
7. Enterprise governance, audit, observability, usage metering and cost guardrails.
8. Full test matrix, recovery drills, security review and release evidence.

## Acceptance rules

- A component is implemented only when its code, tests and ownership boundaries are inspected.
- A test pass proves only the tested behavior, not production readiness.
- No live provider availability is claimed without a real runtime probe.
- No model-generated claim is marked verified without explicit evidence.
- No external side effect occurs without authorization and approval appropriate to its risk.
- Every milestone records changed files, tests executed, failures, remaining blockers and evidence.
- Branch protection: keep all changes on this development branch; open a draft PR targeting the existing development integration branch only if needed. Never target `main` or `master`.

## Current status (2026-11-11)

- Branch created from existing ƎllE/Omni development work.
- Trusted HS256 identity primitive added; XP_TOKEN remains a distinct service credential.
- `xparallel/enterprise_auth.py` now enforces signed identity claims and role-based actions on ƎllE, Omni, Parallel Research and XParallel dispatch user API routes. Workspace and actor are derived from the signed token, not request JSON/query parameters.
- Focused authorization tests added and wired into the XParallel CI workflow.
- No trusted login adapter currently mints these identity tokens for an authenticated end user. The token issuer is a server-side primitive only; upstream login and authoritative membership lookup remain prerequisites before user access can be activated.
- The current enterprise UI does not yet complete the login-to-identity-token flow. Do not claim end-to-end user activation.
- Existing 113-component register still requires source-by-source verification. NexAI and IDEAS remain separate and their independent branches are readiness/audit branches, not runtime integrations.
- GitHub Actions XParallel Integration Tests run #153 completed successfully, including the added HTTP tenant-isolation and zero-cost chat tests.
- No production deployment, production configuration change, default-branch merge or paid resource was made.


## Optional NexAI identity provider

A separate development branch in `axali-sys/nexai-platform` implements a NexAI-session-authenticated identity assertion endpoint. NexAI verifies its own active user and workspace membership, then issues a 15-minute HS256 assertion with issuer `nexai-platform` and audience `axaliai-enterprise`. The XParallel identity verifier supports configured issuer/audience checks. This does not merge or absorb NexAI. Browser SSO/consent and the enterprise UI handoff remain outstanding. No shared secret or production connection has been configured.


## NexAI authorization-code protocol update

The independent NexAI development branch now contains the server-side authorization-code + PKCE S256 protocol: exact redirect allow-list, explicit consent requirement, hashed 90-second one-time codes, atomic redemption, confidential server-to-server exchange, and a current active-user/workspace-membership recheck before issuing the signed assertion. NexAI CI run #59 passed Ruff and the full pytest suite. This is not end-to-end SSO yet: the consent UI, AI Enterprise callback handler, confidential exchange client and AI-owned session creation remain outstanding. No shared secrets or production redirect URIs are configured.
