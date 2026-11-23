# Memory Recovery Protocol (MRP)

Status: development implementation; not yet runtime-integrated or production-verified.

## Purpose

Recover workspace memory from a previously captured snapshot without silently
crossing workspace boundaries, overwriting unrelated data, or trusting corrupt
records.

## Implemented API surface

- `xparallel.memory_backup.create_snapshot(workspace_id, db_path=None)`
  Captures the workspace's current source records into an immutable snapshot row.
- `verify_snapshot(snapshot_id, workspace_id, db_path=None)`
  Checks snapshot format, workspace ownership, item count, manifest SHA-256,
  and each record's content SHA-256.
- `list_snapshots(workspace_id, limit=20, db_path=None)`
  Lists snapshot metadata only.
- `xparallel.memory_recovery.recover_snapshot(...)`
  Supports scoped `merge` or `replace` restoration after authorization and
  explicit scope are supplied.

## Recovery sequence

1. Authenticate the requesting principal and resolve its workspace server-side.
2. Require explicit snapshot ID, source workspace, target workspace, and mode.
3. Require authorization and explicit scope. Cross-workspace restoration must be
   separately authorized by the caller's policy layer.
4. Verify snapshot manifest and each record before mutation.
5. Re-read the snapshot in the write transaction to reduce TOCTOU exposure.
6. For merge, reject conflicting record IDs; identical content hashes are
   idempotent. For replace, delete only the explicitly selected target workspace.
7. Commit the SQLite transaction and return counts/status, not memory content.
8. Audit the operation using minimal metadata and no payload or credentials.

## Safety properties

- Corrupt or missing snapshots fail closed.
- Snapshot lookup is constrained by its source workspace.
- Recovery never accepts a caller-supplied payload.
- Replace is scoped to one workspace; other workspaces remain untouched.
- Recovery does not claim to restore external replicas, conversations, secrets,
  identity credentials, or files outside the Memory Vault.

## Important limitations / next integration work

- The current snapshot is stored in the same SQLite database as the vault.
  It protects against logical deletion and some data corruption, but not loss
  of the entire database/device or an ephemeral serverless filesystem.
- SHA-256 detects accidental alteration; it is not a signature or authenticity
  proof against an attacker able to alter both payload and digest.
- Production requires durable off-device snapshot storage, authenticated
  signatures or trusted manifests, key management, restore drills, retention
  policy, and authenticated API integration.
- The current API functions are not yet wired into the HTTP routes, repair shop,
  or OmniMemory lifecycle UI. No production readiness is implied.
