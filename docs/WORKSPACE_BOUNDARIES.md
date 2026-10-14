# Unity AI Voice Interface — Workspace Boundaries

## Account model

Unity AI Voice Interface is the shared account and application shell. It may provide shared sign-in, account settings, accessibility preferences, and a workspace launcher. **It is not one blended product UI.** Each workspace below must retain its own product identity, layout, navigation, terminology, and user flows.

## Separate workspaces

| Workspace | Product purpose | UI boundary |
|---|---|---|
| **Axaliai** | General-purpose AI interface for conversation, reasoning, and user-directed assistance | Its own chat-first assistant design. Do not label it “Omni”, and do not place Omnibox, UnitAI, or XParallel controls in its primary navigation. |
| **Omnibox** | A separate workspace/product design; its precise feature scope should be defined in its own product specification | Own visual identity, home screen, navigation, and workflows. Do not treat “Omnibox” as a mode or synonym for Axaliai. |
| **UnitAI** | A separate AI workspace/product design | Own visual identity and user flows. It may use shared platform services only through explicit interfaces; its design must not be absorbed into Axaliai or Omnibox. |
| **XParallel** | Separate AI infrastructure and isolated execution/build environment for running, testing, and routing work | Own infrastructure-oriented design, environment/status views, approval gates, execution results, and safety controls. It is not an Axaliai chat theme or a tab inside Axaliai. |

## Shared account, separate products

- Keep the existing repository, account, authentication, API services, Git history, routes, and workflows intact.
- Use a **workspace launcher/switcher** to enter each product. Switching workspaces changes the product surface, not the user account.
- Shared services (identity, entitlements, provider adapters, audit events, and approved APIs) must be behind explicit contracts. Sharing backend services does not imply sharing UI or branding.
- Each workspace owns its own navigation, copy, design tokens, interaction model, and tests. Do not reuse another workspace's branding or menu labels merely because the apps share an account.
- Cross-workspace actions must be explicit, permission-checked, and show which workspace is receiving the request. XParallel execution still requires the existing approval/security model.
- Do not imply a workspace is connected, live, or operational unless a real health/API check confirms it.

## Current change

The Axaliai Squarespace embed is being kept Axaliai-only: its navigation and workspace label should not present Omnibox, UnitAI, or XParallel as Axaliai modes. The other three workspace designs should be implemented as separate entry surfaces in the same Unity AI Voice Interface account.

## Acceptance checklist

- [ ] One account can reach each workspace through a workspace launcher.
- [ ] Axaliai, Omnibox, UnitAI, and XParallel each have a distinct home screen and visual system.
- [ ] No product's primary navigation contains another product's features as if they were its own.
- [ ] Shared sign-in and account settings work without collapsing workspace identity.
- [ ] Workspace-specific routes, permissions, health status, and tests are verified independently.
- [ ] No production deployment or merge occurs without the user's explicit approval.
