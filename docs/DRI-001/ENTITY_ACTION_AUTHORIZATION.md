# XParallel Entity Action Authorization — Draft 0.1

## Purpose

Specify the authorization decision after identity proof. This policy is deliberately separate from key registration, entity registration, capability verification, and runtime execution.

## Required trust chain

1. A trusted authentication adapter verifies the human/organization/workspace session.
2. The adapter resolves a server-side subject and confirms that subject is bound to the entity owner through an approved ownership process.
3. The entity registry reports an active entity.
4. The key registry reports an active signing key.
5. A trusted capability evaluator reports the requested capability as verified (not merely declared by the entity).
6. An administrator/owner approval process creates an explicit, expiring grant.
7. The policy engine matches the exact workspace, subject, entity, key, capability, action, and resource scope.
8. Only then may a separately controlled runtime consider executing the action.

## Deny-by-default policy

The prototype accepts a trusted identity context and a set of explicit grants. It denies if authentication is absent, owner subject differs, entity/key is inactive, capability is not verified, or no exact unexpired approved grant matches.

- No wildcard or prefix scope matching.
- No grant is inferred from a manifest.
- No capability is trusted because an entity claims it.
- A valid signature proves key possession only; it does not create a permission.
- Decision output includes a machine-readable reason for audit and debugging.

## Important integration gap

The current XParallel HTTP service uses a shared bearer token and a client-supplied workspace identifier. Its existing workspace context is not a verified user/organization identity provider. Therefore this policy primitive is **not wired into public or private execution routes**. A trusted authentication adapter, verified owner-to-entity binding, persistent grant repository, signed action envelope/replay protection, and runtime enforcement are required before API integration.

## Production acceptance requirements

- Replace shared-token-only identity with authenticated principals and workspace membership.
- Derive subject/workspace from verified server-side session claims, never request JSON.
- Store ownership bindings and grants in a transactional repository with audited approval/revocation.
- Verify signed action envelopes, timestamps, unique request IDs, and replay protection.
- Enforce policy immediately before every tool, connector, file, network, or sandbox action.
- Add policy decision audit events and independent tests for cross-tenant isolation.
- Independent threat modeling and security review before production use.
