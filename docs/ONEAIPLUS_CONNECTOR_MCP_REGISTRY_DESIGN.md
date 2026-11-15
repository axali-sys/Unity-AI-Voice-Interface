# Oneaiplus Connector, MCP Server, and MCP Registry Design

Date: 2026-11-14
Status: architecture baseline; implementation not yet connected

## Product placement

Oneaiplus owns a unified Integrations and Connectors area. It must expose three distinct but related capabilities:

1. **Custom connectors** — user-managed connections to external APIs and services, including HTTP APIs and OAuth-based providers.
2. **MCP servers** — Model Context Protocol endpoints that expose tools/resources/prompts to authorized Oneaiplus modules and agents.
3. **MCP registry** — a catalog and lifecycle manager for discovering, reviewing, registering, enabling, disabling, updating, and revoking MCP server definitions.

The registry is not itself an execution engine. It stores reviewed definitions and policy metadata. Runtime discovery and invocation happen through a separately governed connector/MCP gateway.

## Navigation and information architecture

Use one Integrations entry with three first-class tabs:

- **Connectors** — built-in and custom API integrations.
- **MCP Servers** — configured server endpoints, transport, authentication reference, health, capabilities and ownership.
- **MCP Registry** — discoverable server catalog, installation/review state, version, publisher, trust and compatibility metadata.

Each entry should have a details view with permissions, connection status, last verification, supported capabilities, audit history, and explicit disable/revoke controls.

Do not collapse Omnibox into the integrations catalogue: Omnibox remains the universal command/search surface; Integrations is the configuration and governance surface.

## Registry record model

A registry entry should contain:

- stable server ID and canonical name
- publisher/owner identity and verification status
- description, tags, category and documentation URL
- server endpoint or package reference (never executable code embedded in metadata)
- supported transport and protocol version
- declared tools/resources/prompts and their schemas
- version, release channel, checksum/signature where applicable
- required scopes and requested permissions
- data classification and network access requirements
- compatibility constraints
- review state: draft, pending_review, approved, rejected, suspended
- installation state: not_installed, installed_disabled, enabled, error, revoked
- timestamps and audit actor references

Never treat publisher-supplied metadata or tool descriptions as trusted instructions. Registry entries are untrusted data until reviewed.

## Custom connector model

A custom connector definition should include:

- stable connector ID and display name
- base URL and allowed hostnames
- authentication mode: none, OAuth, API key, or managed secret reference
- permitted HTTP methods and route patterns
- request/response schema declarations
- timeout, rate limit and retry policy
- scopes, data classification and owner
- connection health and last verified timestamp
- enabled/disabled/revoked state

Secrets must be stored in server-side secret storage and referenced by opaque IDs. Never return raw secret values to the browser, model context, logs, or audit records. Avoid placing credentials in query strings.

## MCP server runtime boundary

MCP execution must pass through a server-side gateway. Browser clients and model prompts must not call arbitrary MCP endpoints directly.

The gateway must:

1. Resolve an enabled registry/server record.
2. Verify server identity and transport policy.
3. Authenticate using a server-side secret reference.
4. Enforce per-server and per-tool allowlists.
5. Validate tool arguments against declared schemas.
6. Apply timeout, rate, payload-size and concurrency limits.
7. Apply user/workspace authorization and data classification rules.
8. Require explicit human approval for consequential or external side effects.
9. Record invocation outcome and sanitized audit metadata.
10. Support immediate disable/revocation and invalidate cached credentials/sessions.

A successful health check is not proof that every tool is safe or operational.

## Governance and approvals

Use least privilege and deny by default. A connector being installed does not mean it is enabled; enabled does not mean every tool is authorized.

Separate these states:

- catalog availability
- installed/registered
- authenticated/connected
- enabled
- authorized for a specific user/module/action
- approved for a particular consequential invocation

Approval must be scoped to the exact proposed action, target, and relevant arguments. A changed action requires fresh approval.

Revocation applies to unauthorized or disallowed work inside XParallel and to connector/MCP credentials as appropriate. It must not interfere with ordinary Oneaiplus chat or block read-only workspace navigation.

## Audit events

Record: actor, workspace, connector/server ID, tool name, requested action class, approval reference, allow/deny decision, timestamp, duration, outcome, sanitized error category, and correlation ID.

Never log bearer tokens, API keys, full authorization headers, or sensitive payloads. Audit records should be append-only for normal authenticated users.

## Initial $0 implementation sequence

1. Build the registry UI using static, clearly labeled sample entries and local development fixtures; do not claim they are connected.
2. Define database tables and row-level security only after a verified isolated database is available.
3. Implement server-side metadata CRUD and owner/workspace authorization.
4. Add custom connector configuration with secret references; no secrets in client storage.
5. Add MCP server registration and a read-only capability/health inspection path.
6. Add a gateway with allowlists, schema validation, limits, approval gates, audit, and revocation.
7. Add one test MCP server in a local isolated environment and verify the full lifecycle.
8. Connect external services only after explicit user authorization and a zero-cost assessment.

## Current verified Lovable workspace facts

The workspace connector catalogue currently exposes a GitHub API connector and a number of MCP catalog entries. The workspace's custom connector list currently reports zero configured custom connectors. The available catalog entries are not evidence that a connector is installed, authenticated, or connected.

Lovable's catalog MCP entries are mostly marked available but not connected. Oneaiplus must keep its own registry metadata and runtime governance rather than assuming the Lovable workspace catalog is a connected Oneaiplus runtime.

## Non-goals and safety constraints

- No automatic execution of arbitrary registry entries.
- No client-side storage of credentials.
- No production deployment or main-branch merge as part of this design.
- No paid service or credit consumption without approval.
- No changes to Render or Vercel connections in this milestone.
- NexAI and IDEAS remain independent products.
- XParallel remains a distinct governance and execution layer integrated with Oneaiplus, not a replacement for the connector registry.
