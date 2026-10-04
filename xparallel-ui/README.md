# XParallel Standalone UI V1

Standalone interface for the existing XParallel infrastructure.

**Product boundary**
- Axaliai is the public/development-layer front door.
- XParallel is the dedicated parallel development workspace.
- Browser code contains no XP_TOKEN or payment credentials.
- Execution remains human-approval gated.

**Workspace**
Overview · Projects · Solutions · Agents · Sandbox · Evidence · Graph · Deploy

This V1 is a responsive static UI surface. The next integration step is to connect the views to the existing XParallel API through a server-side gateway/proxy. Never expose XP_TOKEN to browser JavaScript.
