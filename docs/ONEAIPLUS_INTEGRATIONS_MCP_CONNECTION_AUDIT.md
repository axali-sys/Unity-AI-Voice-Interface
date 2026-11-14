# Oneaiplus Integration and MCP Connection State Audit

Date: 2026-11-15
Workspace: ff79e3a0f86ba2c60f87
Canonical project: c2232890-a16d-4289-b2f8-c8de6365a7b4
Status: Read-only workspace connector inspection.

## Executive result

The Lovable workspace exposes a broad connector catalogue, including standard integrations, seamless integrations and MCP catalog entries. The catalogue being enabled does not mean an integration is connected to the user's account or available to Oneaiplus runtime code.

The installed/custom connector query returned zero connectors (total: 0). The MCP catalogue entries returned by the workspace API were all marked available and enabled, but disconnected.

## Observed MCP catalogue entries

Amplitude, Atlassian, Canva, Confidence Experiments, Confidence Flags, Excalidraw+, Figma, Fullstory, Granola, Hex, HeyGen, HubSpot, Linear, Loom, Miro, Notion, Paper, Polar, PostHog, Sanity, Sentry, Siteimprove, Supermetrics, Wispr Flow and n8n.

All returned MCP catalogue entries had is_connected=false. These are catalog availability states, not authenticated sessions or tested tool calls.

## Useful standard/seamless catalogue categories

The catalogue includes GitHub, GitLab, Google Workspace services, Microsoft services, Slack, Discord, Telegram, WhatsApp Business, Notion, Linear, Sentry, PostHog, n8n, AWS, Cloudflare, Supabase, AI Gateway and other providers. These are workspace catalogue records only. This audit did not connect accounts or invoke provider actions.

## Installed/custom connector state

- Custom/installed connector list: empty.
- Total returned: 0.
- No custom MCP server registration was observed through this connector listing.
- Render and Vercel account-level connection remains intentionally deferred.

## Implications for Oneaiplus Integrations UI

The UI must distinguish these states explicitly:
1. Catalogued — provider appears in the supported catalogue.
2. Registered — a custom endpoint or server record has been created.
3. Authenticated — account or service credentials have been configured.
4. Connected — a real handshake or provider health check succeeded.
5. Authorized — the user has granted specific scopes/capabilities.
6. Enabled — runtime policy permits discovery/use.
7. Approved for action — a consequential operation has explicit approval.

Never show a catalogue item as connected merely because is_enabled=true. Never infer that MCP tools are callable from a catalogue entry. Do not expose secrets in the UI, prompt context, logs or browser bundles.

## Recommended implementation order

1. Create separate Integrations tabs for Connectors, MCP Servers and MCP Registry; keep Omnibox as a distinct command/search surface.
2. Add read-only status cards based on actual backend connection records, not catalogue flags.
3. Add server-side credential references and OAuth/token lifecycle handling without returning secrets to clients.
4. Add per-server tool allowlists, argument schemas, timeouts, rate and payload limits, and redacted audit events.
5. Require explicit per-action approval for side effects; implement disable/revoke controls.
6. Test disconnected, expired credential, unauthorized scope, malformed arguments, timeout, provider outage and revocation cases.

## Non-actions

No connector was installed, enabled, authenticated, connected, or invoked by this audit. No credentials were requested or changed. No code, database, project, donor, deployment or billing state was modified.
