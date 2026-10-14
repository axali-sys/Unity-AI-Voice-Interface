# Unity AI Voice Interface — Workspace Boundaries and Shared Intelligence

## Account model

Unity AI Voice Interface is one account and application shell. It can share sign-in, account settings, accessibility preferences, entitlements, and approved backend services. **One account does not mean one blended product UI.** Each workspace retains its own product identity, design system, navigation, terminology, and user flows.

## Four distinct workspaces

| Workspace | Purpose | Design boundary |
|---|---|---|
| **Axaliai** | General-purpose AI interface for conversation, reasoning, and user-directed assistance | Dedicated chat-first assistant experience. Not the home for the other products' controls. |
| **Omnibox** | Independent product/workspace design | Own home screen, navigation, terminology, and workflows; not an Axaliai mode. |
| **UnitAI** | Independent AI workspace/product design | Own visual identity and interaction model; not absorbed into Axaliai or Omnibox. |
| **XParallel** | AI infrastructure and isolated execution/build environment for running, testing, routing, and fixing programs | Own infrastructure-oriented design, environment/status views, approval gates, execution results, and safety controls; not merely an Axaliai chat theme. |

## Shared Parallel Intelligence and AI Mixer

**Parallel Intelligence is a shared platform capability used by all four workspaces.** It is not owned by, or exclusive to, XParallel.

The shared AI Mixer coordinates the configured AI providers/adapters and any explicitly enabled tools, then synthesizes one response for the current request. The mixer must use the active workspace's identity and task context to shape that response:

- **Axaliai:** general-purpose conversation, reasoning, and user-directed assistance.
- **Omnibox:** the response should reflect Omnibox's separately defined product purpose and request context.
- **UnitAI:** the response should reflect UnitAI's separately defined product purpose and request context.
- **XParallel:** the response should respect execution/workspace context, approval requirements, and infrastructure safety boundaries.

Workspace-specific context must be explicit in the request contract (for example, a validated workspace identifier and task context), not inferred from visual branding alone. The mixer should return one synthesized answer plus auditable provider evidence where available: provider/model ID, latency, token usage, response hash, and explicit reasons for skipped providers. If no providers are configured or all fail, return a clear unavailable/error state; do not silently pretend a normal response was produced.

## Shared account, separate product surfaces

- Keep the existing repository, account, authentication, routes, API services, Git history, and workflows intact.
- Use a **workspace launcher/switcher** to enter each product. Switching workspace changes the product surface and request context, not the user account.
- Shared identity, provider adapters, mixer, audit events, and approved APIs sit behind explicit service contracts. Sharing backend capabilities does not mean sharing UI or branding.
- Each workspace owns its navigation, design tokens, interaction model, and tests.
- Cross-workspace actions must be explicit and permission-checked, and must identify the receiving workspace. XParallel execution still requires its existing approval/security model.
- Never report a workspace or provider as connected/live unless a real health/API check confirms it.

## Current Axaliai interface change

The Axaliai embed remains Axaliai's own design. It now labels Parallel Intelligence and the AI Mixer as a **shared intelligence layer**, while making clear that Omnibox, UnitAI, and XParallel remain distinct workspace designs.

## Acceptance checklist

- [ ] One Unity AI Voice Interface account can enter all four distinct workspaces.
- [ ] All four workspaces can use the same shared Parallel Intelligence/AI Mixer service.
- [ ] Each request carries validated active-workspace context, and the mixer applies the corresponding response profile.
- [ ] Provider evidence, skipped-provider reasons, and unavailable states are explicit and auditable.
- [ ] No product's primary navigation absorbs another product's features as if they were its own.
- [ ] Shared sign-in and account settings work without collapsing workspace identity.
- [ ] Workspace-specific routes, permissions, health status, and tests are verified independently.
- [ ] No production deployment or merge occurs without the user's explicit approval.
