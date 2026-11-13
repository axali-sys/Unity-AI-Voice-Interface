# M2.10 — Restricted Docker Execution Boundary

## Status

Implemented as a hardened local Docker-runner configuration and unit-tested command builder. Not approved as a production multi-tenant sandbox. No live hostile-code or production environment test was performed.

## Controls

- Runner refuses to start unless XP_RUNNER_IMAGE is pinned to an immutable sha256 image digest.
- Execution uses an unprivileged UID/GID (65532:65532).
- Container network is disabled; root filesystem is read-only.
- Linux capabilities are dropped; no-new-privileges and Docker's default seccomp profile are requested.
- Private IPC namespace, CPU/memory/swap/PID limits, file-size and open-file limits are applied.
- /tmp is a bounded noexec/nosuid/nodev tmpfs.
- Only a disposable temporary workspace is mounted; no host credentials, source checkout, Docker socket, or home directory is mounted.
- Input files have per-file, total-size, count, path-traversal, and base64 validation limits.
- Stdout and stderr are drained concurrently with bounded retained output (10,000 bytes per stream by default); excess output is discarded while pipes continue draining. The result records whether either stream was truncated.
- The Docker CLI is launched in a separate process group and that group is killed on timeout. This does not yet prove that every Docker-daemon-managed container is terminated on every host/runtime failure; container-ID tracking and daemon-side cleanup verification remain required before hostile public workloads.
- The execution command remains an explicit test command supplied to the runner and is treated as untrusted code.

## Required configuration

Set XP_RUNNER_IMAGE to a trusted image reference ending in @sha256: followed by the image's full 64-character digest. A mutable tag is deliberately rejected. The digest must be obtained and reviewed by the operator; this milestone does not download or select an image on the user's behalf.

Other XP_RUNNER_* settings have bounded defaults. Invalid or unsafe limits block execution.

## Important threat-model limitations

Docker shares the host kernel and Docker daemon. A daemon compromise, kernel vulnerability, unsafe daemon configuration, malicious image, resource-exhaustion gap, or container escape can compromise the host. This runner is not equivalent to a microVM, gVisor, Kata Containers, Firecracker, or a dedicated hostile-code execution service.

Before any public or multi-tenant use, require a dedicated disposable worker host or stronger isolation boundary, daemon access separation, image signature/provenance verification, egress enforcement outside the container, filesystem quotas, robust process-tree cleanup, concurrency quotas, independent penetration testing, and security review. Do not expose Docker socket access to application code.

## Integration boundary

This milestone hardens the existing local runner module only. It does not wire entity action authorization to HTTP routes, automatically execute entity tasks, or establish production identity. The Verified Entity Action Gate remains a separate adapter-ready policy primitive. Execution must remain disabled until trusted identity, capability evidence, grants, approval, and sandbox policy are integrated at the same server-side boundary.

## Verification

Unit tests inspect workspace validation, strict resource bounds, Docker command construction, digest pinning, no network, read-only root, dropped capabilities, absence of host credential mounts, bounded stdout/stderr capture, and timeout process-group cleanup. These tests verify local process behavior and configuration construction, not that a live Docker host enforces every control.


CI note: the test suite includes explicit checks for digest pinning, workspace path and size limits, non-root ownership, Docker command hardening, and the blocked state when Docker is unavailable.


Open hardening items: verify daemon-side container termination on timeout, add concurrency and host-level disk quotas, and independently validate the Docker host configuration. Do not expose this runner to untrusted public workloads until those controls and stronger isolation are independently reviewed.
