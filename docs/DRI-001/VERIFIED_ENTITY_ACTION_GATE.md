# Verified Entity Action Gate — Draft 0.1

## Purpose

Compose the existing identity context, capability verification evidence, and approved permission grants into one fail-closed action decision.

## Decision chain

1. Authenticate the caller through a trusted host adapter.
2. Resolve the entity owner binding, entity status, signing-key status, capability version, and exact deployed artifact digest from trusted server-side records.
3. Ask the capability verification laboratory for the status of that exact entity/capability version/artifact digest.
4. Load authoritative approved grants from a trusted grant repository.
5. Call the deny-by-default entity action policy with the derived capability status and exact grant set.
6. Return a machine-readable decision and a compact evidence reference. No action is executed by this module.

## Fail-closed behavior

Any missing identity, missing artifact binding, unavailable grant repository, verification storage failure, malformed trusted context, or dependency exception produces a denial. A declared, failed, inconclusive, expired, suspended, revoked, or artifact-mismatched capability cannot pass the policy.

## Mandatory trusted adapters

- Authentication must provide a server-verified subject and workspace.
- Entity-context resolution must use server-side ownership, entity, key, version, and artifact records; it must not trust request-body assertions.
- Grant loading must use the authoritative governance repository, never caller-supplied grants.
- Verification status must be read from the capability laboratory for the exact artifact digest and capability version.

## Explicit limitations

This is a composition primitive with injected host adapters. It is not connected to HTTP routes or execution tools. It does not establish authentication, owner legitimacy, key validity, artifact provenance, or sandbox safety by itself. Existing HTTP routes continue to use their prior shared-token/workspace model. Production use requires real adapters, transactional and durable repositories, authenticated signed action requests, replay protection, policy checks immediately before every consequential operation, and independent security review.

## Safety

The gate makes authorization decisions only. It never runs a tool, changes files, calls external services, or executes an entity action. A successful decision is not proof that an action is safe in every context; it is evidence that configured identity, capability, and grant conditions matched at decision time.
