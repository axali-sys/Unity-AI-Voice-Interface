# M2.11 — Trusted Host Adapters and Enforcement Boundary

Status: **partial implementation; not activated for HTTP execution**.

## Implemented in this isolated branch

- `xparallel/trusted_host_adapters.py` composes the existing Digital DNA registry, Ed25519 key store, governance grant registry, capability verification lab, and decision-only action gate.
- Authentication is an injected server-side session verifier. The adapter accepts only an authenticated principal with a non-empty subject and a strictly validated workspace identifier.
- Entity records are loaded from the authenticated workspace, not from client-supplied workspace claims.
- Signing-key status is loaded from the scoped key registry and checked against workspace/entity/key identifiers.
- Capability version is read from the registered entity record, but a self-declared capability status is never trusted.
- Executable artifact identity must be supplied by a separate trusted host artifact resolver, and the returned SHA-256 digest is bound into the existing verification gate.
- Active grants are loaded directly from the governance repository for the authenticated workspace and entity.
- `build_action_gate()` returns the existing decision-only gate. It does not execute a job or grant permission by itself.
- Tests exercise the real local registries and Ed25519 proof-of-possession path, authentication failure, workspace isolation, missing keys/capabilities, and the rule that a manifest cannot self-assert an artifact digest.

## Required host responsibilities / blockers

1. Supply a real server-side authentication/session verifier. The repository's current shared bearer-token and client-workspace HTTP model is not a trusted user/entity identity provider.
2. Supply an authoritative artifact resolver that binds a version to the exact immutable artifact that the sandbox will execute.
3. Supply trusted governance role administration and verifier authorization. The local SQLite repositories are development stores only.
4. Add a route middleware integration only after the authentication contract is independently reviewed. Do not accept subject, owner, workspace, key status, grant, capability status, or artifact digest from request JSON.
5. Add route-level integration tests against the eventual authenticated host and prove that every execution route checks the gate immediately before execution.
6. Keep consequential execution disabled until approval tickets, revocation checks, signed receipts, durable storage, and sandbox enforcement are integrated.

## Acceptance result

The concrete local adapter layer is implemented and testable, but M2.11 is **not complete**. No production HTTP route is connected, no authentication provider is configured, and no end-to-end execution is enabled. Passing local tests does not prove production authentication or security.
