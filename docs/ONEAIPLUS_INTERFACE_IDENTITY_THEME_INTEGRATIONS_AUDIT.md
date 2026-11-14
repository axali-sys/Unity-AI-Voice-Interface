# Oneaiplus Interface Identity, Theme, and Integration Management Audit

Date: 2026-11-15
Scope: read-only source inspection of canonical Oneaiplus and donor projects, plus a capability check of available Lovable connector operations. No source code, database, project settings, integrations, or deployments were changed.

## 1. Canonical identity consistency

The canonical Lovable project is named Oneaiplus, but inspected interface source still uses legacy OneAI labels:
- src/components/AppShell.tsx navigation says OneAI Home.
- The sidebar Brand component renders OneAI.
- The inspected HomeChat.tsx prompt says Ask OneAI anything….
- The chat server system instruction identifies the assistant as OneAI.

Decision: Oneaiplus is the canonical workspace and product identity. Update user-facing workspace labels and assistant context to Oneaiplus in a future controlled source edit. Preserve historical names in repository history, donor identities, and technical references where they describe an existing product or service. Do not globally rename unrelated projects or XParallel.

## 2. Theme preference

The OneAI Workspace donor ThemeToggle.tsx toggles the document dark class, stores oneai-theme in browser localStorage, and initializes component state from the current document class. It does not read the stored preference before rendering, does not define an account-level preference, and does not synchronize across devices. It is a useful interaction reference, not a complete persistence implementation.

Recommended Oneaiplus design:
1. Add a stable theme preference with system/light/dark choices.
2. Load the preference before or during app initialization without a visible theme flash.
3. Persist locally for immediate, offline-friendly behavior.
4. Optionally synchronize to the authenticated account only after a canonical preference schema and owner RLS policy are approved.
5. Keep theme preference independent from provider credentials and connector permissions.

## 3. Navigation and module consolidation

The canonical AppShell already groups modules into Core, Intelligence, and Platform. This is a sound base for Oneaiplus as the single workspace. Preserve the canonical shell and selectively absorb useful donor workflows, not replace it with a donor shell.

Recommended navigation: Home / Command Center; Projects and Workspace; Assistant; Parallel Intelligence; Omni; XParallel; Build Studio and Repair Shop; UnitAI and Jellybox; Integrations with distinct Connectors, MCP Servers, and MCP Registry views; Security / UIDaaS; Settings and activity.

NexAI and IDEAS remain independent products and must not be presented as merged Oneaiplus modules or have their identity/security boundaries absorbed.

## 4. Connector and MCP management reality

The Lovable workspace connector catalogue and custom connector inventory are separate from the Oneaiplus app's own integration-management interface.

Previously inspected workspace catalogue entries included standard connectors and MCP catalogue entries, many marked available/enabled but not connected. The custom connector inventory returned zero configured entries. This does not establish that Oneaiplus itself has a working connector runtime.

The Lovable connector operation available to this workflow returns a dashboard URL for the user to add a connector; it does not programmatically install a connector. The current discovered Lovable operation set includes project listing, project read, drafts, knowledge, connector catalogue, custom connector listing, and dashboard deep-link generation. It does not expose a project GitHub source-control link/unlink operation.

Implementation architecture for Oneaiplus Integrations:
- Connectors: configured external service connections, connection state, scopes, ownership, test status, and disconnect action.
- Custom Connectors: user-defined endpoint and auth metadata; secrets stored only server-side or in a secret manager, never returned to browser code.
- MCP Servers: server registration, endpoint validation, transport, authentication reference, health, tool discovery, allowlists, timeouts, and disable/revoke controls.
- MCP Registry: discoverable server/tool metadata with publisher, version, source, trust status, permissions, review status, and install history.
- Execution gateway: server-side mediation, strict tool/schema validation, scoped credentials, rate/size limits, audit events, and explicit approval for consequential actions.

A catalogue listing is not a connected integration; a connected integration is not automatically authorized for execution; and a listed MCP tool is not proof that a secure execution gateway exists.

## 5. Source-control linkage blocker

The Lovable tools currently exposed for this workflow can inspect projects and files, create/read drafts, inspect connector catalogues, and manage project knowledge. They do not expose a GitHub source-control connect/disconnect action for an existing Lovable project.

The separate GitHub connector can manage the axali-sys/Unity-AI-Voice-Interface repository, but that does not prove the canonical Lovable Oneaiplus project is linked to that repository or that the Lovable editor is writing to the documentation branch.

Required verification before application edits:
- In the canonical Oneaiplus Lovable editor, inspect project GitHub integration settings.
- Confirm the exact repository owner/name and selected branch.
- Confirm the canonical app source files appear in that repository and match the inspected Lovable commit.
- Confirm whether the project uses its own branch and how draft changes are isolated.
- Do not link the XParallel backend repository blindly if it would replace or conflict with the canonical TanStack frontend source.

Until that linkage is confirmed, GitHub documentation commits remain architecture records only; they do not alter the Oneaiplus application.

## 6. Next implementation sequence

1. Establish and verify canonical Oneaiplus source-control linkage to the correct source repository.
2. Align the visible brand and assistant labels to Oneaiplus.
3. Add robust theme initialization and preference persistence.
4. Consolidate donor workspace records into canonical data structures, without duplicate audit tables.
5. Implement Connectors, MCP Servers, and MCP Registry with server-side secrets and permission boundaries.
6. Add chat history with explicit retention and deletion controls.
7. Add server-enforced audit events and integration approval/revocation tests.

## Verification and non-actions

- Inspected canonical src/components/AppShell.tsx, src/components/HomeChat.tsx, and src/server/chat.server.ts.
- Inspected donor src/components/ThemeToggle.tsx.
- Reviewed the currently exposed Lovable tool capability list for project source-control and connector operations.
- No app source files changed.
- No connectors were installed or authenticated.
- No credentials were read or written.
- No project was renamed, merged, unpublished, or deployed.
- No database writes or paid services were used.