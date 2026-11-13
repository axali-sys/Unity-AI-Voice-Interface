# M2.14 — Durable Storage and Recovery Foundation

Status: **local SQLite repository foundation; migration of existing subsystem stores is not complete**.

## Implemented

- `SQLiteStore` provides explicit transaction boundaries using `BEGIN IMMEDIATE`, rollback on failure, full synchronous mode, and foreign-key enforcement.
- Versioned migrations have ordered version numbers and SHA-256 checksums; reapplying an identical migration is idempotent and changing an applied migration is rejected.
- `SQLiteJSONRepository` provides a simple workspace-scoped repository interface for structured records.
- Backup uses SQLite's online backup API and validates the destination with `PRAGMA integrity_check`.
- Restore requires a host authorization adapter, checks source integrity and schema version, creates a pre-restore safety backup, restores, then checks integrity.
- Backup retention only prunes regular, non-symlink `.sqlite3` files matching an explicit prefix and keeps at least one backup.

## Not yet completed

- Existing Digital DNA, identity, governance, messaging, verification, execution and receipt stores have not all been migrated behind shared repository interfaces.
- No PostgreSQL or distributed durable backend is configured or tested.
- No automated scheduled backups, off-site replication, encryption-at-rest, key management, disaster recovery rehearsal, retention/legal policy, or production recovery-time/recovery-point objectives are established.
- Backup files are local plaintext SQLite files; production storage needs reviewed encryption, access controls and external retention.
- This foundation is not a claim of multi-node consistency or high availability.

## Acceptance status

The local storage/recovery foundation and tests are added. M2.14 remains partial until existing subsystem stores are migrated, durable backend conformance is tested, and backup/restore is rehearsed against a real deployment architecture.
