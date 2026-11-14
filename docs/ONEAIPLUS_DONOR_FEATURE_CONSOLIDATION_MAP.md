# Oneaiplus Donor Feature Consolidation Map

Date: 2026-11-15
Canonical target: Lovable project `c2232890-a16d-4289-b2f8-c8de6365a7b4`

This report compares the canonical project and three donor projects by reading their file inventories and selected source files at their current commits. It is a source audit, not a claim that donor code has been merged.

## 1. Canonical project — retain as the foundation

The canonical Oneaiplus project already has:
- TanStack Start + React + TypeScript + Tailwind.
- Shared app shell and navigation, with Home, Projects and 14 named enterprise sections.
- Owner-focused authentication and middleware.
- Server functions for projects, diagnostics and owner operations.
- Jellybox memory and audit-event persistence.
- XParallel public health/access/system probes.
- A module-status gate that currently denies privileged execution.
- Read-only diagnostics and deployment controls.

Keep this architecture. Do not replace the app with a donor project or with the Next.js frontend from the XParallel repository.

## 2. OneAI Workspace donor — highest-value functional donor

Project ID: `c7f1e64a-d093-4b2c-9c09-7b8a47bbd2f6`
Current commit inspected: `9978295b23a833de87a291c3f0c234efc51134c1`

### Features worth selectively porting
- A more general workspace record model: section, name, content, status, owner and updated timestamp.
- Per-user CRUD server functions with validated inputs and owner scoping.
- Workspace activity/audit read surface.
- Account provider and OAuth sign-in/out controls.
- Dark/light theme toggle with local preference.
- Chat route and AI SDK streaming adapter.
- Read-only GitHub repository context selection for AI tasks.
- Health checks that distinguish database reachability, XParallel health and AI configuration.
- Section-specific work modes (answer, research, compare, plan, code, repair, agent, recall).

### Important limitations and risks
- The donor's workspace records use a separate `workspace_records` table and audit table. Do not copy its migrations into the canonical database until schema, RLS, owner policy and data-isolation strategy are reconciled with canonical `projects`, `memories` and `audit_events`.
- Donor chat uses Lovable AI Gateway and has already encountered insufficient-credit (HTTP 402) constraints. Preserve honest unavailable/error states; do not create fake assistant responses.
- GitHub repository context is read-only; it is not a GitHub source-control binding for the canonical Lovable project.
- The donor has a different account-provider composition. Do not duplicate canonical auth or bypass canonical owner-only authorization.
- The UI's labels and mode names do not prove the associated model/agent capability is live.

Recommendation: port reusable workspace record UX and selected theme/chat UI only after mapping them onto canonical server functions, existing auth and existing tables. Prefer a migration plan that reuses canonical persistence rather than creating duplicate tables.

## 3. Pixel Perfect Replica donor — selective security/control-center reference

Project ID: `f81f245c-8558-4b6d-bc5a-9ccaff7727d9`
Current commit inspected: `c83cda619251b8796f91077a4450693581896351`

### Features worth studying
- Authenticated route grouping.
- A product/status control-center dashboard with status counts and status labels.
- Separate core ecosystem and independent-product groupings.
- Role vocabulary: admin, operator, member.
- A people-and-roles administration view.
- Permission helper tests for role distinctions.

### Important limitations and risks
- Its branding and product data model are AXALIAI-specific and should not be transplanted literally into Oneaiplus.
- Its permission UI reads roles and mutates role assignments through Supabase client calls. Any port must be backed by verified server-side authorization and restrictive RLS; hiding a button is not authorization.
- Do not merge its role system into the canonical owner-only security model until a deliberate multi-user/workspace authorization design exists.
- Its test file covers a small set of pure permission helpers; it does not establish end-to-end RLS or authorization correctness.

Recommendation: use the dashboard grouping and status taxonomy as a design reference. Reuse neither the schema nor role mutation code without a security review.

## 4. Pixel Perfect Replay donor — visual/navigation reference only

Project ID: `91552ebf-59d2-4c69-b5be-d9e0ff926909`
Current commit inspected: `3e99bffcafe71abc213728600341af3b4362ee18`

The inspected source is primarily a responsive OneAI shell/navigation and screenshot recreation. It substantially overlaps with the OneAI Workspace donor and adds no clearly unique backend capability in the inspected inventory.

Recommendation: preserve this project unchanged. Use it only as a visual reference if a specific layout detail is missing from the canonical shell.

## 5. Consolidation matrix

| Capability | Canonical Oneaiplus | Workspace donor | Replica donor | Recommended action |
|---|---|---|---|---|
| App shell/navigation | Present | Present | Present | Keep canonical shell; port only useful visual details |
| Authentication | Owner-only | Account/OAuth provider | Authenticated routes + roles | Keep canonical auth; design roles separately |
| Workspace records | Projects table | General section records | Product catalogue | Extend canonical model carefully; avoid duplicate tables |
| AI chat | Present, provider constrained | Streaming chat route | Not primary focus | Port streaming UX only with verified provider availability |
| Theme toggle | Not confirmed in inspected canonical shell | Present | Not unique | Port theme preference if desired |
| Audit | Canonical audit events | Workspace audit list | Admin dashboard activity | Reuse canonical append-only audit foundation |
| GitHub | Diagnostic connector | Read-only repo context | Not primary | Keep server-side connector contract; don't confuse with source control |
| Role administration | Owner guard | No team roles | Admin/operator/member UI | Defer until server-enforced multi-user authorization is designed |
| XParallel | Health probes + denied execution gate | Health-only probe | Not primary | Keep canonical XParallel boundary and current deny-by-default gate |
| MCP/custom connectors | Architecture documented | No full runtime registry | Not primary | Implement as separate server-side subsystem |

## 6. Recommended implementation order

1. **Foundation:** establish canonical Oneaiplus GitHub source-control connection in Lovable's own project settings. Do not repoint either donor repository.
2. **Workspace UX:** selectively port named records, list/search, status, export and responsive layout into canonical sections using canonical persistence and auth.
3. **Theme:** add persistent theme preference without copying a second app shell.
4. **Chat:** reconcile the donor's streaming route with canonical `/api/chat`, provider gateway limits and XParallel private chat contract. No browser-held secrets.
5. **Audit:** standardize all mutations to append audit events server-side; preserve append-only restrictions.
6. **Connectors/MCP:** build registry metadata and secure server-side invocation separately from Lovable's own connector catalogue.
7. **Roles:** only after workspace membership, roles, RLS and server authorization are formally designed and tested.
8. **XParallel execution:** only after host-side authorization, approvals, exact grants, revocation and evidence checks are demonstrably enforced.

## 7. Current change boundary

- No donor project was edited, renamed, deleted or merged.
- No canonical application source files or database tables were changed.
- No Lovable AI builder was invoked; no AI credits were consumed.
- No production publish/deploy or merge to `main` occurred.
- Render and Vercel account connections remain postponed.
- The only repository change for this milestone is this documentation file on the isolated branch `oneaiplus/unification-foundation-2026-11-14`.

## 8. Verification limits

The report is based on Lovable file inventories and selected source reads at the commits listed above. It does not claim the donor applications were freshly built, tested or deployed during this audit. The canonical Oneaiplus app source remains at its previously verified commit until its supported GitHub source-control connection is established.
