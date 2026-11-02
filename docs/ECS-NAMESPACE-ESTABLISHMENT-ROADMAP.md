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


## Monthly monitoring log — 2 November 2026

### Official ICANN status

- The authoritative 2026 Round Applicant Guidebook is now V3-2026.10.07, published 7 October 2026. It supersedes V2 and is the version to use for future readiness work.
- ICANN's 2026 application window closed 12 August 2026. No later application window for a subsequent round was identified in the official program materials checked on this date. Do not infer or announce a next-round date.
- The official APS public snapshot lists 481 applicants and 1,615 applications (last published 7 October 2026). ICANN separately reported 1,616 paid applications on 22 September 2026. APS notes that one application (WDO2627T-T45217) remains under administrative check and is not shown in the public Applications list; this appears to explain the one-record difference, but the exact .ecs search remains incomplete.
- THE EXACT .ECS APPLICATION STATUS IS UNVERIFIED. The APS site is the authoritative source, but its interactive application/string filter and full downloadable record set could not be completely queried in this monitoring pass. Search-engine indexing is not a substitute for a complete APS query. No conclusion is made that .ecs was or was not applied for. Applicant identity, application ID/status, and any replacement-string relationship remain unconfirmed. Repeat a direct APS search for exact primary string .ecs, replacement strings, and applicant records after the portal's next publication.
- ICANN's published timeline identifies 17 November 2026 as String Confirmation Day. The community input and objections period is scheduled for 17 November 2026–16 March 2027. The prioritization draw is expected in the first half of 2027; string evaluation and later application evaluation milestones remain subject to ICANN updates.
- The replacement-string period following Reveal Day closed 21 October 2026. Do not assume an applicant can now change a string outside the Guidebook's defined change processes.
- No pre-registration or reservation of oneai.ecs or xparallel.ecs is available through this project. Both remain proposed aliases only.

### Current fees, support, entity, and RSP requirements

- Standard 2026 Round gTLD evaluation fee: USD 227,000 per application. Conditional evaluations and contention resolution can add fees. After delegation, the 2026 Base RA also provides for a quarterly registry fixed fee (the agreement states USD 6,437.50 per quarter as of 1 January 2025, subject to adjustment), a per-transaction fee (USD 0.2575 as of that date, applying only after the 50,000-transaction threshold), and a one-time USD 5,000 Trademark Clearinghouse access fee plus applicable Sunrise/Claims transaction charges. These contract amounts are not a current quote; confirm the live ICANN fee schedule before any financial model. RSP, legal, security, escrow, continuity, registrar, staffing, and other operating costs are additional.
- The 2026 Applicant Support Program application period closed 19 December 2025. Qualified applicants could receive a 75–85% evaluation-fee reduction (the published range is USD 34,500–56,750), plus capacity development, pro bono professional services, applicant counseling, and other support. A new applicant cannot newly enter the closed 2026 ASP process; future-round support terms are unknown.
- Applicants must be established legal entities in good standing. Individuals, sole proprietorships, and not-yet-formed entities are not eligible. Background screening includes the entity and relevant directors, officers, major shareholders, and controlling/parent persons.
- Under the Standard financial profile, the applicant must show long-term funding, financial statements and projections, a three-year operating plan, and cash on hand of at least USD 50,000 + 25% of the application fee per string, subject to the USD 300,000 cap. For one standard-profile string at the current fee, that arithmetic is USD 106,750. This is in addition to the application fee and does not represent the full cost of running a registry.
- The 2026 RSP Evaluation Program's second/final submission period closed 12 August 2026. Its evaluated-provider list continues to be updated as providers clear evaluation. A future applicant must identify one or more evaluated RSPs; self-provisioning critical registry services requires successful ICANN RSP evaluation and is not a shortcut around the requirements.

### Registry operating requirements and founding-name options

- The 2026 Base Registry Agreement was approved by the ICANN Board on 12 March 2026. It requires, among other things, compliant DNS, DNSSEC, EPP, RDAP/registration-data publication, data escrow, registry continuity, reporting, registrar access, rights-protection mechanisms, and contractual compliance.
- Applicants must demonstrate financial and operational capacity for long-term registry operation, including security planning and a DNS Abuse plan. The Guidebook's abuse commitments include a dedicated abuse contact, a public abuse-reporting channel, documented complaint handling, appropriate resources and timely response, and periodic zone scanning/reporting for phishing, malware, botnets, pharming, and spam used to deliver other DNS abuse.
- There is no current founder priority or right to either second-level name. The 2026 Base RA does create a conditional future mechanism: a contracted registry operator may register and activate up to 500 names necessary for operation or promotion of its TLD, subject to the Agreement and rights-protection mechanisms. Whether oneai.ecs or xparallel.ecs qualifies would require documented justification and legal/policy review; this is not a current reservation or guarantee.
- A registry operator may also withhold additional names under its reserved-name policy, but withheld names are not activated in DNS. Releasing a withheld name is subject to the Registry Agreement and applicable rights-protection mechanisms; reservation is not a promise of eventual allocation to the operator or a founder.
- A generic-string TLD may not restrict registrations exclusively to one person/entity and its affiliates (closed generic prohibition). A community-based application may define a real, clearly delineated community and ICANN-evaluated Community Registration Policies, but this is not a founder-only shortcut. Community Priority Evaluation is a contention-resolution mechanism, not a general founder-name priority.
- Trademark Sunrise is a future launch-stage rights-protection mechanism for eligible rights holders with a verified Trademark Clearinghouse record/Signed Mark Data file. It does not create rights now, does not guarantee a particular domain name, and would operate under the then-current Registry Agreement and TMCH requirements. No OneAI or XParallel trademark/SMD entitlement is established by this roadmap.

### Parallel ecosystem implementation status

Checked against branch feat/xparallel-ai-verse-founding-identities, head commit 53424b08cbdbd5c31f7cc142b9e709cc8eb7606d:

- oneai.core and xparallel.verse remain the stable internal identity keys.
- xparallel/identity_directory.py contains read-only proposed identity records. Their .ecs labels are explicitly proposed_unregistered, verification is unverified, and endpoint bindings are empty.
- GET /verse/identities is present behind the existing authenticated read-role check.
- xparallel/identity_bindings.py provides a SQLite foundation for creating, listing, and revoking HTTPS endpoint bindings. New bindings remain endpoint_unverified; the challenge is generated but this branch has no configured external proof verifier or identity-binding HTTP route. A dedicated binding test module was not present in the inspected branch tree.
- Therefore roaming identity is partially scaffolded, not end-to-end operational or production-verified. No live DNS/registrar integration, public .ecs resolution, endpoint verification, purchase, DNS mutation, merge to main, or production deployment is evidenced by this check.
- The founding identity specification remains the design reference. No changes to the repository's identity keys or existing history are proposed in this monitoring entry.

### Sources checked on 2 November 2026

- ICANN 2026 Round overview: https://newgtldprogram.icann.org/en/application-rounds/round2
- Authoritative Applicant Guidebook V3-2026.10.07: https://newgtldprogram.icann.org/sites/default/files/documents/new-gtld-program-2026-round-applicant-guidebook-current-en.pdf
- Application Publication and Statistics: https://newgtldprogram-aps.icann.org/statistics
- ICANN Reveal Day announcement and milestones (7 October 2026): https://www.icann.org/en/announcements/details/icann-reveals-2026-round-applications-for-new-generic-top-level-domains-07-10-2026-en
- Applicant Support Program: https://newgtldprogram.icann.org/en/application-rounds/round2/asp
- Registry Service Provider Evaluation Program and evaluated-provider list: https://newgtldprogram.icann.org/en/application-rounds/round2/rsp
- Board-approved 2026 Base Registry Agreement (12 March 2026): https://itp.cdn.icann.org/en/files/registry-agreements/base-registry-agreement-12-03-2026-en.pdf
- ICANN 2026 Round Resources: https://newgtldprogram.icann.org/en/application-rounds/round2/resources
