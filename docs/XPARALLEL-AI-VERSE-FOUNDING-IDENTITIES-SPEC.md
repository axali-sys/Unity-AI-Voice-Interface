# XParallel AI Verse: Founding Identity Implementation Specification

**Status:** Proposal for review on a development branch  
**Repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Scope:** OneAI and XParallel founding identities, the Parallel Verse identity directory, and future `.ecs` naming readiness  
**Safety:** This specification does not claim that `.ecs` exists as a delegated TLD, that either name is reserved, or that the proposed features are implemented or production-verified.

## 1. Product decision

The XParallel AI Verse is the connected ecosystem for AI identities, agents, workspaces, and services.

Two founding identities are intended:

| Identity | Intended future name | Role |
|---|---|---|
| OneAI | `oneai.ecs` | Human-facing AI workspace and command center |
| XParallel | `xparallel.ecs` | AI Verse interoperability, discovery, coordination, and governed execution infrastructure |

These are **aspirational names only**. Do not describe them as registered, reserved, guaranteed, or currently resolvable. A future `.ecs` TLD would require the appropriate ICANN process and delegation. The availability of second-level names would then depend on registry policies, launch rules, applicable rights, and the state of the namespace at that time.

## 2. Architecture principles

1. **Preserve the existing repository and history.** Extend the current OneAI/XParallel application; do not replace it with a new starter.
2. **Stable internal identity first.** The ecosystem must function without `.ecs`. Internal IDs are canonical; domains are optional aliases.
3. **Explicit status.** UI and APIs distinguish `concept`, `local`, `registered-in-directory`, `verified`, `provider-confirmed`, and `production-verified` where applicable. Never imply that directory registration proves ownership of an internet domain.
4. **No fake operations.** A mock registrar, mocked DNS result, or simulated identity verification must be labeled as demo/test data.
5. **Authentication and tenant isolation.** Resolve principal and workspace membership server-side. Never authorize a request from a client-supplied workspace ID alone.
6. **Least privilege.** Identity listing, profile editing, DNS modification, domain purchase, and agent execution are distinct permissions.
7. **Approval and evidence.** Consequential changes require explicit approval and produce an audit event and a verifiable outcome.
8. **Zero-cost development by default.** Use existing infrastructure and local SQLite for development. No paid service, domain purchase, production deployment, or DNS mutation is authorized by this specification.
9. **Privacy by design.** Publish only fields explicitly marked public; never expose secrets, private endpoints, access tokens, or internal account identifiers.

## 3. Logical component model

- **OneAI Workspace:** user-facing command center and the entry point to assistant, AI Mixer, Build Studio, Repair Shop, and ecosystem identity views.
- **XParallel:** policy boundary and interoperability layer for agent/service discovery and approved connections.
- **Parallel Verse:** persistent conceptual world containing identity records, agents, spaces, relationships, and append-only events.
- **UIDaaS:** future identity/session/device trust and permission layer. Integrate only to the degree actually implemented and verified.
- **Omni:** orchestration lifecycle for plans, approval, execution, verification, and evidence.
- **Jellybox:** future artifact/SmartBlock storage; do not imply consensus or distributed storage exists without separately tested implementation.
- **Domain Provider Adapter:** an interface to an actual registrar/DNS provider. Keep provider-specific credentials server-side and the adapter disabled until configured.

These are logical boundaries, not a claim that every component is currently wired end-to-end.

## 4. Founding identity record

Create or seed the following identities in a development/test environment only. They must be clearly labeled as proposed internal identities, not domain registrations.

### OneAI
- `identity_key`: `oneai.core`
- `display_name`: `OneAI`
- `identity_type`: `workspace`
- `ecosystem_role`: `founding_workspace`
- `preferred_domain_label`: `oneai.ecs`
- `domain_status`: `proposed_unregistered`
- `public_description`: `The unified AI workspace and command center for research, building, repair, coordination, and approved execution.`

### XParallel
- `identity_key`: `xparallel.verse`
- `display_name`: `XParallel AI VERSE`
- `identity_type`: `ecosystem_infrastructure`
- `ecosystem_role`: `founding_infrastructure`
- `preferred_domain_label`: `xparallel.ecs`
- `domain_status`: `proposed_unregistered`
- `public_description`: `The interoperability and discovery infrastructure connecting independent AI agents, services, and workspaces under explicit policy and verification.`

Internal keys are permanent identifiers, not DNS names. Do not make an identity's primary key equal to a domain string.

## 5. Suggested data model

Implement only after inspecting existing schemas and choosing compatible migrations. Avoid duplicating current Parallel Verse tables.

### Identity
- `id`: opaque UUID/ULID primary key
- `identity_key`: unique stable key (e.g. `oneai.core`)
- `display_name`
- `identity_type`: workspace | infrastructure | agent | service | organization
- `owner_principal_id`: nullable only for seeded system identities; otherwise required
- `workspace_id`: server-derived tenant boundary
- `public_description`
- `capabilities`: validated structured list
- `public_endpoint`: optional HTTPS URL; validated and subject to SSRF protections before any server-side fetch
- `verification_status`: unverified | evidence_pending | verified | revoked
- `domain_label`: nullable alias
- `domain_status`: none | proposed_unregistered | provider_pending | provider_confirmed | revoked
- `created_at`, `updated_at`, `deleted_at` (soft deletion where needed)

### IdentityEvent (append-only audit/event stream)
- `id`
- `identity_id`
- `actor_principal_id`
- `event_type`
- `event_payload_redacted`
- `occurred_at`
- `correlation_id`
- `evidence_ref` (optional; never place credentials in evidence)

### DomainBinding (only when actual provider integration exists)
- `id`
- `identity_id`
- `fqdn`
- `provider`
- `provider_resource_id`
- `ownership_status`
- `verification_method`
- `verified_at`
- `last_checked_at`
- `provider_response_ref` (redacted, non-secret evidence)

Do not create a live `DomainBinding` for `oneai.ecs` or `xparallel.ecs` until the namespace exists and a real provider/registry confirms the registration.

## 6. API design (proposed; inspect existing route conventions before implementation)

All routes must use existing application patterns and be namespaced consistently. These are proposed contracts, not assertions that routes exist.

- `GET /api/verse/identities`: list identities visible to the authenticated principal; filter public visibility and tenant membership server-side.
- `GET /api/verse/identities/{identity_key}`: fetch one visible identity.
- `POST /api/verse/identities`: create an identity; authenticated owner and workspace must be derived server-side.
- `PATCH /api/verse/identities/{id}`: update only permitted fields; write audit event.
- `POST /api/verse/identities/{id}/verification-challenges`: create a challenge only for supported verification methods; do not report success until evidence is validated.
- `GET /api/verse/identities/{id}/events`: authorized, paginated event history.
- Future provider routes for domain availability, registration, renewal, and DNS must be separate, rate-limited, audited, and disabled until a real provider is configured.

If existing Parallel Verse routes already provide equivalent functionality, extend them rather than introducing duplicate routes. Preserve backwards compatibility unless tests and explicit review justify a change.

## 7. Domain provider adapter

Define a provider-neutral interface with methods such as:
- `check_availability(fqdn)`
- `get_quote(fqdn, term)`
- `create_registration(order, approval_context)`
- `get_registration_status(provider_resource_id)`
- `list_dns_records(fqdn)`
- `apply_dns_change(fqdn, change, approval_context)`

Requirements:
- Use a mock adapter only in tests/demo mode and label all results as simulated.
- Live mode must fail closed if credentials or provider configuration are missing.
- Never invent availability, prices, registration status, renewal dates, or DNS propagation.
- Require explicit confirmation for purchases and high-impact DNS changes.
- Validate provider responses; use idempotency keys for registration/order actions when supported.
- Keep API keys in server-side secrets only; redact secrets from logs and audit events.
- Add rate limits, abuse monitoring, retry limits, and clear provider error states.
- Do not integrate a paid provider until separately approved.

## 8. Identity verification and trust

Verification is evidence-specific. A profile existing in the directory does not mean that its owner controls a domain or that an AI agent is safe.

Possible future levels:
1. **Directory record:** profile created; no ownership claim.
2. **Owner authenticated:** an authenticated account controls the platform profile.
3. **Domain control proven:** a real DNS or HTTP challenge has been validated against a domain in a live namespace.
4. **Endpoint ownership proven:** a challenge has been validated for the declared endpoint.
5. **Capability attested:** specific capability claims have evidence and an issuer.
6. **Revoked/expired:** previous evidence is no longer valid.

Show the verification method, timestamp, issuer, and scope. Avoid a single vague “trusted AI” badge. Do not crawl arbitrary endpoints without SSRF defenses, timeouts, allow/deny rules, and network egress controls.

## 9. UI requirements

Add an **AI Verse / Identities** view within the existing OneAI navigation, not a separate replacement app.

Required states:
- Founding identities: OneAI and XParallel, visibly marked `Proposed founding identity`.
- Domain badges: `Proposed — not registered` for `oneai.ecs` and `xparallel.ecs`.
- Directory browse/search and identity detail view.
- Owner and capabilities, with private fields hidden from public views.
- Verification evidence and status history.
- Clear empty, loading, unauthorized, provider-unconfigured, provider-error, and stale-data states.
- Admin controls separated from public discovery.
- Mobile-responsive layout and accessible labels.

Do not display a fake “available”, “registered”, “verified”, or “live” status. Never present a clickable purchase action for `.ecs` until the TLD is legitimately available through a real provider.

## 10. Security, privacy, and reliability acceptance criteria

- Every non-public read and every mutation checks authenticated principal and tenant membership server-side.
- Client-supplied `workspace_id` is never sufficient authorization.
- Users cannot modify identities owned by another tenant without explicit permission.
- Domain purchase and DNS changes require a separate permission and a clear confirmation step.
- Provider credentials never appear in client bundles, responses, or logs.
- All mutation events are auditable with actor, time, target, result, and redacted evidence.
- Invalid URLs, private-network endpoints, redirects, oversized responses, and timeouts are safely handled.
- Demo fixtures are marked as fixtures in both API and UI.
- Delete/revoke behavior is defined; revocation invalidates future claims but preserves necessary audit evidence.
- Tests cover authorization, cross-tenant isolation, schema validation, provider failures, idempotency, redaction, and stale verification.
- No production readiness claim without passing tests, live provider verification, persistent storage verification, and a documented rollback plan.

## 11. Delivery sequence

### Stage A — Inspect and map
- Inspect current Parallel Verse schemas, routes, authentication, and tests.
- Map this spec to existing modules.
- Identify route/table overlap and document the migration plan.
- No code changes to main and no production action.

### Stage B — Read-only directory
- Add founding identity fixtures and read-only identity views.
- Clearly mark domain labels as proposed/unregistered.
- Test tenant visibility and public/private field filtering.

### Stage C — Owner-managed identities
- Add authenticated create/update and append-only audit events.
- Add role checks and cross-tenant tests.
- Add verification-state model without claiming real domain verification.

### Stage D — Provider sandbox
- Select a provider only after reviewing eligibility, costs, renewal economics, and API terms.
- Add sandbox integration behind a feature flag.
- Verify provider responses and failure paths.
- Keep live purchases and DNS mutations disabled by default.

### Stage E — Live provider integration (separate approval required)
- Configure production secrets securely.
- Test real availability, quotes, registration status, renewal, DNS, support and recovery.
- Obtain explicit approval before any purchase, DNS mutation, merge to main, or production deployment.

### Stage F — Future .ecs registry readiness
- Track ICANN's official new-gTLD timetable and Applicant Guidebook.
- Investigate legal applicant structure, registry-service provider options, technical/security obligations, financial requirements, applicant support, and launch policy.
- Establish a compliant policy for proposed founding names only if .ecs is approved/delegated and applicable rules permit it.
- Never sell pre-registration or imply priority rights before a valid mechanism exists.

## 12. Verification report format

Every implementation milestone should report:
- exact branch and commit
- files/routes/schema changed
- tests actually run and their results
- mocked versus live integrations
- security checks performed and remaining
- real provider responses, with secrets redacted
- unresolved risks
- whether merge, purchase, DNS change, or deployment occurred (default: no)

## 13. Out of scope for this change

- Applying for or claiming ownership of `.ecs`
- Registering or purchasing any domain
- Reserving or guaranteeing `oneai.ecs` or `xparallel.ecs`
- Paid provider activation or paid infrastructure
- Production deployment or DNS changes
- Merging existing draft PRs or changing `main`
- Claiming UIDaaS, Jellybox, Omni, verification, or live provider functionality that has not been implemented and independently tested

## 14. Sources to maintain

Use the latest official ICANN New gTLD Program page, Applicant Guidebook, application-round announcements, applicant-support guidance, and Registry Service Provider information. Record the retrieval date and link for each material rule or fee. The guidebook and future round rules govern over this planning document.
