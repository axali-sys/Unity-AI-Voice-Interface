# XParallel entity permission revocation switch

The XParallel workspace exposes an entity permission revocation control in
`public/xparallel.html`. It inspects one grant and, after an explicit
confirmation and reason, calls the authenticated private endpoint:

- `GET /governance/grants/{grant_id}`
- `POST /governance/grants/revoke` with exactly `grant_id` and `reason`

Revocation is permanent for that grant. A revoked grant cannot be reinstated;
the entity must request a new grant and obtain a separate approval. Temporary
access pauses should use the registry's suspension operation instead.

## Security boundary

These endpoints are deliberately fail-closed. They require
`XP_AUTH_MODE=jwt`, a valid configured session verifier, and a host-injected
`EntityGovernanceRegistry`. The host must construct that registry with
trusted server-side adapters for session authentication, entity ownership,
and governance authorization, then call
`configure_entity_governance_registry(registry)` during its trusted bootstrap.
The registry's own `revoke` and `get` methods revalidate the bearer session
and enforce workspace/operation authorization. Browser-supplied roles,
workspace IDs, and owner claims are never accepted.

The default server does not fabricate these adapters. Until the host injects
them, the API returns HTTP 503 and the UI keeps the revocation control
unavailable. Legacy shared-token mode is intentionally insufficient for
entity-governance revocation.

Every successful revocation is written to the registry's append-only
governance event history. Revocation does not apply to this ChatGPT
conversation or to unrelated entities/workspaces.
