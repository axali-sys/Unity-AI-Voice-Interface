# XParallel Entity Governance and Permission Registry — Draft 0.1

## Purpose

Provide persistent, workspace-scoped governance for entity permission requests and grants. Owners request narrowly scoped authority; a separate trusted governance principal approves; grants can be suspended, reinstated, or revoked with reasoned audit events.

## Trust model

Three host-provided adapters are mandatory:
- `authenticate(session)`: resolves a verified server-side principal and workspace. Request JSON is never accepted as identity.
- `resolve_owner(workspace_id, entity_id)`: resolves the current trusted owner subject.
- `authorize_governance(principal, entity_id, operation)`: checks whether the principal can approve, suspend, reinstate, revoke, or audit for that entity.

The prototype does not implement a login system, organization membership, legal identity checks, or governance role management. It depends on adapters to do those things correctly.

## Grant lifecycle

`requested → pending → approved → suspended → approved` or `revoked`.

- The verified owner requests a grant for one entity, key, capability, action, exact resource scope, and bounded expiry.
- A separately authorized governance principal approves the request. The requester cannot approve their own request.
- Only approved and unexpired grants are exposed by `active_grants`.
- Governance-authorized principals may suspend, reinstate, or revoke grants. Each state change requires a reason.
- Revocation is terminal. A replacement permission requires a new request and approval.
- A suspended grant can only be reinstated while its original expiry remains in the future.

## Security properties and limits

- Deny by default; exact resource-scope matching only; no wildcards.
- Workspace-scoped database keys and queries.
- Grant records and event history are stored separately. Events are append-only through this API, but a privileged database operator can alter SQLite files.
- Grant expiry is enforced when active grants are read and by the existing policy evaluator.
- This module does not verify entity status, signing-key status, or capability evidence itself. The caller must pass those trusted facts to the authorization policy.
- No API routes or execution runtime are changed in this milestone.
- The existing HTTP server's shared bearer token is not a trusted per-user governance identity. Do not wire this module to that token as a substitute for an identity provider.

## Production requirements

Integrate a real session/identity provider; verified owner-to-entity binding and membership; persistent governance-role assignments; approval notification and separation-of-duties policy; transactional DB migration and backup; signed approval records or external append-only audit; immediate revocation propagation; rate limits; expiry cleanup; policy checks at each action boundary; and independent security review.

## Status

Local SQLite governance prototype and unit tests only. No production integration, deployment, or automatic grant issuance.
