# Axaliai to XParallel Gateway V1

The initial access architecture is:

User -> Axaliai application or website -> Axaliai gateway -> XParallel -> controlled sandbox -> evidence -> human approval -> real execution.

The Axaliai client is the authorized front door. The browser should call Axaliai application routes; the gateway handles identity, organization scope and XParallel access.

V1 capabilities:
- ask
- route
- build
- solution
- verify
- graph search

Boundaries:
- Execution remains human-approval gated.
- Payment capture remains disabled.
- Organization scope must come from authenticated identity.
- Application credentials stay server-side.

Strategic position: build a proprietary, trusted infrastructure layer and network effect rather than blocking competitors.