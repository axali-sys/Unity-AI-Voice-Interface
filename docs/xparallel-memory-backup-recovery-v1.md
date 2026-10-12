# Memory Vault Backup and Recovery V1

- Configure `XP_MEMORY_DB` to a persistent writable SQLite file.
- Configure `XP_MEMORY_BACKUP_DIR` to a separate durable directory or mounted volume.
- Create a SQLite-consistent snapshot, then verify its SHA-256 manifest and SQLite `quick_check` before restoring.
- Restore preserves a pre-restore snapshot when the target database already exists.

This provides local integrity-checked recovery only. It is **not** encrypted or off-site backup, and it is not proof of cloud durability. Use a separately managed encrypted/off-site copy for disaster recovery. Do not store sensitive content until storage access, encryption, and deployment persistence are configured and verified.
