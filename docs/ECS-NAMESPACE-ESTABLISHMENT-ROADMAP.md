# ECS Namespace Establishment Roadmap

**Status:** Active planning document; $0-start; no purchases, paid commitments, DNS changes, merges to `main`, or production deployment authorized.  
**Repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Related specification:** [XParallel AI Verse Founding Identities](./XPARALLEL-AI-VERSE-FOUNDING-IDENTITIES-SPEC.md)

## Executive decision

Proceed on two coordinated tracks:

1. **ECS ecosystem track:** establish the namespace model, roaming identity resolution, trust and governance rules, and a usable prototype in the existing OneAI/XParallel project.
2. **Official .ecs registry track:** prepare an evidence-based application-readiness package and monitor ICANN's official New gTLD Program. Do not describe `.ecs` as a delegated/public TLD or imply that a future round is open.

The project has two stable logical identities:
- `oneai.core` — OneAI workspace and command center.
- `xparallel.verse` — XParallel AI Verse interoperability and discovery infrastructure.

The proposed future names `oneai.ecs` and `xparallel.ecs` are **aspirational aliases only**. They are not represented as registered, reserved, available, or guaranteed.

## Important current registry facts

As checked on 27 October 2026:

- ICANN's 2026 New gTLD application window closed on 12 August 2026. The round's applications have been published for public review. The current official application portal and statistics are the source of truth for applied-for strings and application status.
- ICANN's published milestones say String Confirmation Day is scheduled for 17 November 2026, with the community input and objections period scheduled from 17 November 2026 to 16 March 2027. The prioritization draw is expected in the first half of 2027.
- The latest Applicant Guidebook page identifies version V3-2026.10.07 as the authoritative guidebook as of 7 October 2026.
- The standard gTLD evaluation fee stated in the current guidebook is USD 227,000 per application. A qualifying Applicant Support Program applicant may receive a substantial discount, with the stated range USD 34,500–56,750; qualification and final fees are not guaranteed. These amounts do not include all legal, registry, technical, operating, and contingency costs.
- A $0 start can cover research, planning, governance drafts, prototypes, and partner/funding preparation. It cannot fund a normal paid gTLD application or guarantee a registry launch.

Sources:
- [ICANN 2026 Round overview](https://newgtldprogram.icann.org/en/application-rounds/round2)
- [ICANN Applicant Guidebook](https://newgtldprogram.icann.org/en/application-rounds/round2/guidebook)
- [ICANN 2026 Round application statistics and public applications](https://newgtldprogram-aps.icann.org/statistics)
- [ICANN announcement: 2026 Round applications revealed, milestones](https://www.icann.org/en/announcements/details/icann-reveals-2026-round-applications-for-new-generic-top-level-domains-07-10-2026-en)

This document does not assert that `.ecs` is or is not present in the complete live application data. Before making that claim, search the official application portal for exact `.ecs` entries, replacement strings, applicant identity, and current status; record the result and date. Do not infer string status from general search-engine results.

## Track A — Build the ECS ecosystem now

### A1. Namespace and governance (no cost)

- Keep internal identity keys separate from DNS names and host locations.
- Decide and document what “ECS” formally stands for before public claims or brand filings; do not silently assume an expansion.
- Define who can issue identities, verify ownership, revoke identities, change endpoints, and publish capability claims.
- Distinguish internal identity, domain alias, owner authentication, endpoint verification, and real registry/provider confirmation.
- Publish a versioned namespace and identity policy in the repository.

### A2. Roaming identity model (development only)

- Extend existing Parallel Verse architecture only after inspecting routes, schemas, authentication, and tests.
- Use existing tables and APIs where equivalent functionality exists; do not duplicate them.
- Map `oneai.core` and `xparallel.verse` to endpoint bindings that can change without changing their identity keys.
- Support local-only operation without a public domain, an external resolver, or a paid provider.
- Verify endpoint changes with authenticated owner approval, challenge evidence, revocation, audit events, expiry, and revalidation.
- Make domain aliases optional. Add `.ecs` aliases only when a legitimate namespace and actual allocation/registration evidence exist.
- Keep live registrar/DNS operations disabled. Any future purchase or DNS mutation requires separate explicit approval.

### A3. Prototype and acceptance tests

- Identity directory can list the two proposed founding identities with clearly labeled status.
- Changing a development endpoint does not change the stable identity key.
- Unauthenticated or cross-tenant users cannot alter identity or endpoint bindings.
- Revoked, expired, stale, and unverified endpoints are not shown as trusted.
- No-`.ecs` mode still works.
- Export/import preserves identity keys and relationships without exporting secrets.
- Provider outage, DNS failure, and resolver failure produce honest degraded states.
- Tests and logs distinguish fixtures/mocks from live evidence.

## Track B — Prepare for official .ecs registry opportunity

### B1. Monitor official process

- Track ICANN's New gTLD Program page, latest Applicant Guidebook, application statistics, String Confirmation Day, objections, evaluation stages, applicant-support guidance, and future-round announcements.
- Confirm whether `.ecs` was applied for in the 2026 round by checking the official application portal and its final/current records. Record applicant name, status, any replacement-string relationship, and date if a record exists.
- Do not contact, challenge, or negotiate with an applicant based on a guess. Obtain qualified legal advice before any rights-related communication.
- Do not claim a next-round opening date until ICANN publishes it.

### B2. Applicant readiness dossier

Prepare drafts only, at no cost:
1. Proposed applicant entity and governance options, with jurisdiction and legal advice to be determined.
2. Mission and public-interest case for an ecosystem connectivity namespace.
3. Financial model, funding strategy, and risk register.
4. Technical registry architecture and registry-service-provider shortlist.
5. Security, DNS abuse, incident response, continuity, escrow, data protection, and disaster recovery policies.
6. Registry/registrar relationship, pricing, launch, reserved-name, dispute, and rights-protection policies.
7. Founder-name policy for `oneai.ecs` and `xparallel.ecs`, subject to applicable rules and fair allocation requirements.
8. Applicant Support Program eligibility investigation; never assume qualification or support.
9. Milestone calendar with official source URLs and retrieval dates.

### B3. Financial gate

- No application, legal engagement, provider contract, application-support payment, domain purchase, or other paid commitment without separate approval.
- The standard 2026-round evaluation fee is a substantial funding requirement, not an amount available in the current $0 budget.
- Treat registry operations as a separate long-term business requiring competent technical operators, legal governance, security operations, support, and durable funding.
- If the next application round is not yet open, use the interim period for readiness, partnerships, and funding rather than claiming an application has been submitted.

## Work sequence and gates

| Phase | Deliverable | Gate |
|---|---|---|
| 0 | Verify current ICANN application data and maintain dated source register | No claims about `.ecs` application status without official evidence |
| 1 | Inspect existing Parallel Verse implementation and write route/schema/test map | No duplicate tables/routes |
| 2 | Implement a read-only founding identity directory on a development branch | Auth and tenant isolation tests pass |
| 3 | Add endpoint bindings and roaming verification in development | Revocation, portability, audit, and no-domain tests pass |
| 4 | Complete applicant readiness dossier and funding plan | No paid commitments |
| 5 | Reassess official ICANN opportunity and eligibility | Requires fresh official evidence and user decision |
| 6 | Live registry/provider application or deployment | Separate explicit approval and confirmed funding required |

## Reporting requirements

For every implementation milestone report the exact branch/commit, files changed, tests actually run, mock versus live status, security checks, unresolved risks, and whether any merge, purchase, DNS change, paid commitment, or deployment occurred.

## Explicit exclusions

This roadmap does not register or reserve `.ecs`, create a public TLD, guarantee the future names, submit an ICANN application, spend money, modify DNS, merge pull requests, or deploy to production.
