# Axaliai Infrastructure Website — Implementation Plan

## Product direction
Axaliai is the umbrella identity for a general AI infrastructure ecosystem. The public website at axaliai.com explains the ecosystem, its architecture, technologies, services, developer resources, research direction, security principles, and contact channels.

IDEAS remains a separate product. Existing XParallel integrations and assistant functionality must be preserved; they must not be represented as complete services unless verified.

## Repository strategy
- Source of truth: this existing repository.
- Base branch: main.
- Website development branch: feat/axaliai-infrastructure-website.
- Do not merge into main or deploy to production without explicit approval.
- Preserve existing Git history, routes, integrations, and environment-variable contracts.

## Hosting decision
Evaluate a hybrid architecture before committing:
- Squarespace remains the domain registrar/DNS management surface.
- Vercel + Next.js is the preferred hosting candidate for the website.
- Existing backend services remain independently hosted.
- No DNS changes, domain transfers, paid services, or production changes without approval.

## Information architecture
1. Home
2. About
3. Infrastructure
4. Technologies
5. AI Systems
6. Solutions
7. Developer Platform
8. API Services
9. Documentation
10. Research & Innovation
11. Security
12. Contact

## Infrastructure concepts
- Intelligence: AI core, cognition, reasoning.
- Orchestration: Omni and workflow coordination.
- Collaborative intelligence: Parallel Intelligence.
- Interoperability and execution: XParallel and gateway services.
- Knowledge: OmniMemory and Knowledge Genome.
- Engineering: Build Studio, AI Repair Shop, developer tooling.
- Foundation: identity, security, observability, compute and storage.

These are product architecture concepts, not claims that every service is already implemented or operational.

## Delivery milestones
1. Audit the existing repository, routes, components, integrations, dependencies, tests, and deployment configuration.
2. Establish design system, shared navigation, responsive shell, and all public page structures.
3. Implement page content and interactive architecture visualizations.
4. Add developer portal and documentation foundation; clearly label unavailable APIs as planned.
5. Integrate only verified services, test accessibility/responsiveness/performance/security, and prepare a preview deployment for review.

## Acceptance criteria
- All navigation and internal links work.
- Responsive mobile and desktop layouts.
- Existing assistant and XParallel functionality remains intact.
- No secrets exposed client-side.
- No simulated integrations presented as operational.
- Tests/build checks documented with actual results.
- Preview and production are separated.
- No production deployment or DNS changes without approval.

## Initial audit findings
- Repository: axali-sys/Unity-AI-Voice-Interface
- Default branch: main
- Existing README describes a Next.js assistant UI and /api/chat proxy to XParallel.
- package.json reports Next.js 14.2.15, React 18.3.1, React DOM 18.3.1.
- Existing branch list contains prior Axaliai redesign and Squarespace bridge work. These must be reviewed for reusable work before implementation; do not assume their contents are merged into main.


## Milestone execution update (2026-11-07)
- Milestone 1: repository structure and key files inspected; historical Axaliai redesign and Squarespace bridge branches were compared with main. They are divergent and were not blindly merged. Existing app was identified as Next.js App Router.
- Milestone 2: a responsive Axaliai public website shell and design system were added to the root route.
- Milestone 3: the page now covers the umbrella identity, infrastructure layers, technology principles, separate product identities, solutions, research and security.
- Milestone 4: developer/API/documentation sections and an API publication policy were added. They intentionally do not advertise unverified live endpoints.
- Milestone 5: existing assistant UI was preserved at /assistant; shared metadata and README were updated. Automated build, browser, accessibility and live backend verification remain pending.
- Contact destination remains intentionally unconfigured until a verified business inbox is supplied.
- No DNS, deployment, paid service, production, or main-branch change was made.
