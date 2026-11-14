# Oneaiplus Unified Enterprise — Integration Foundation

Status: isolated development foundation; not a release or production deployment.
Date: 2026-11-14

## Canonical product decision

Oneaiplus is the single user-facing enterprise workspace and canonical Lovable project.
XParallel is the shared digital infrastructure and governed entity-interoperability layer hosted behind Oneaiplus; it remains a distinct subsystem and security boundary, not a second competing workspace.
The existing Unity-AI-Voice-Interface repository is the source of the XParallel Python service and its existing Next.js assistant/proxy implementation. It is not a replacement for the Oneaiplus Lovable frontend.

NexAI and IDEAS remain independent products and are explicitly out of scope for this consolidation.

## Existing Lovable project sources to consolidate

- Oneaiplus (canonical target): c2232890-a16d-4289-b2f8-c8de6365a7b4
- OneAI Workspace: c7f1e64a-d093-4b2c-9c09-7b8a47bbd2f6
- Pixel Perfect Replica: f81f245c-8558-4b6d-bc5a-9ccaff7727d9
- Pixel Perfect Replay: 91552ebf-59d2-4c69-b5be-d9e0ff926909

The projects are separate source trees. This record is a consolidation map, not evidence that their code has already been copied or merged.

## Source-of-truth boundaries

1. Oneaiplus owns the unified navigation, identity presentation, workspace shell, user experience, module entry points, settings and product-level status.
2. XParallel owns entity identity/Digital DNA, capabilities, discovery, communication, governance, grants, revocation, approval-bound execution, audit/provenance and worker interoperability.
3. The Python service in this repository owns XParallel server-side APIs and must keep privileged tokens and host credentials server-side.
4. Browser code must never receive XP_TOKEN or other host secrets. Oneaiplus should call a same-origin authenticated server proxy; the proxy authenticates the user and enforces workspace scope before calling private XParallel routes.
5. The Oneaiplus Lovable app currently uses a TanStack Start stack. This repository has a Next.js 14 assistant interface plus Python XParallel backend. Do not replace Oneaiplus' framework wholesale. Integrate via a documented HTTP contract and server-side adapter.
6. Lovable AI Gateway-dependent features must show a clear unavailable/provider-not-configured state when credits are exhausted. Do not fake model responses or mark AI-backed features operational without a functioning provider.

## Consolidation map

| Source project | Preserve and absorb into Oneaiplus |
|---|---|
| Oneaiplus | Canonical application shell, current modules, auth, projects, owner controls, Jellybox and audit foundations |
| OneAI Workspace | Useful chat/workspace interactions, conversation presentation and workspace tools, after reviewing auth and API dependencies |
| Pixel Perfect Replica | Reusable visual system, navigation/layout patterns and responsive components, after checking accessibility and duplication |
| Pixel Perfect Replay | Reusable screens/components and interaction patterns not already present in the canonical shell |

Shared UI components should be deduplicated. Keep only one navigation, one session/auth boundary, one settings surface and one project/workspace model. Preserve source histories in their original repositories/projects until the integrated implementation is verified.

## Module boundaries for the unified workspace

- Home / Command Center: status, recent work and enterprise navigation.
- Assistant: conversation UI; provider calls remain server-side and report 402/429/provider errors honestly.
- Builder: source projects, files, change review and build evidence.
- Parallel Intelligence / AI Mixer: provider-independent orchestration contracts; live model synthesis requires configured providers.
- Omni Engine: plans, workflows, schedules and run history; execution requires policy approval.
- UnitAI: reusable agents/workers and lifecycle status.
- Jellybox: persistent user/workspace memory, provenance, search, retention and deletion controls.
- XParallel: entities, Digital DNA, capabilities, discovery, governance, grants, revocation, evidence, audit and execution gates.
- UIDaaS / Security: authentication, role/permission checks, session management and security audit.
- AI Repair Shop: diagnostics, repair proposals, tests and verification records; no silent production repair.
- Deployment Center: environment inventory, release checklist and approval records; no deployment without explicit approval.
- Integrations / Omnibox / Settings: connector inventory, secure configuration status and account preferences.

## XParallel safety constraints

- Public health/access/system endpoints are read-only discovery surfaces.
- Private execution remains disabled unless trusted identity, ownership, capability evidence, exact grant, approval, expiry, resource limits and runtime revocation checks are all enforced by the host.
- Revocation is a security control for unauthorized or no-longer-authorized XParallel work; it is not applied to ordinary assistant conversations.
- Do not merge the open governance-bootstrap PR or enable host governance until the outstanding trusted-identity/owner/admin normalization defects and persistence requirements are corrected and independently tested.
- A local runner, adapter, registry or passing unit test is not evidence of a production-grade hostile-code sandbox or operational distributed network.

## No-credit implementation sequence

1. Keep this branch isolated from main and inventory existing source contracts and tests.
2. Finish a component-level overlap map for the four Lovable projects; choose canonical components from Oneaiplus and record donor components.
3. Define and test a versioned Oneaiplus-to-XParallel server API contract, with mock/fake service tests that require no paid AI provider.
4. Port or recreate reusable frontend components in Oneaiplus' own TanStack Start source only through a source-controlled workflow that does not consume Lovable AI credits.
5. Add feature-completeness and availability states so each module remains useful without paid AI services.
6. Run repository tests, type checks and build checks; record failures and blockers accurately.
7. Provide a reviewable preview and evidence before requesting any merge, publish or deployment approval.

## Explicit non-goals and release gates

- No Render or Vercel connector setup in this milestone.
- No Lovable credit top-up, paid provider, paid infrastructure or purchase.
- No production deployment, publish action, DNS change, main-branch merge or destructive project deletion.
- No migration of NexAI or IDEAS into Oneaiplus.
- No claim that all 113 ecosystem components are operational until each has an implementation, tests, host integration and evidence.

## Verification record

- Main branch base at foundation creation: 142f6ac02c9991229ff5f1054364ce02835804b1
- Working branch: oneaiplus/unification-foundation-2026-11-14
- This document records the architecture and sequence only. It does not claim code consolidation, build success, live service integration or production readiness.
