# XParallel AI Memory Vault — V1

This subsystem is an add-on to the existing `axali-sys/Unity-AI-Voice-Interface` repository.

## V1 behaviour
- Saves recoverable source text in SQLite.
- Deduplicates identical content within the same workspace using SHA-256 fingerprints.
- Supports keyword retrieval and explicit listing/deletion.
- Keeps workspace records isolated at query level.
- Does not claim that summaries, embeddings, or model memory can reconstruct original files.
- Does not yet provide encryption-at-rest, binary-file backup, semantic/vector retrieval, cross-device sync, or tested disaster recovery.

## Configuration
Set `XP_MEMORY_DB` to a persistent writable database path. The default local filename is `xparallel_memory.sqlite3`; ephemeral hosting filesystems must not be treated as durable backups.

## Safety notes
The API must remain authenticated. Use HTTPS, access controls, encrypted storage/backup at the deployment layer, and tested restore procedures before storing sensitive or irreplaceable data. Do not expose this module through public routes until authorization and retention policies are reviewed.

## Next validation
Add unit tests for deduplication, workspace isolation, search, deletion, oversized input, and persistence across process restarts. Then connect memory retrieval to XParallel's existing ask/plan workflow behind authenticated routes.
