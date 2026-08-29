# XParallel V1 implementation

## Runtime path
Axaliai -> XParallel gateway -> `/execute` -> approval gate -> controlled Docker sandbox -> test command -> evidence -> review.

## V1 controls
- Docker-only project execution; the host never evaluates the supplied test command.
- No container network access.
- Read-only container root filesystem with a writable disposable `/workspace` mount.
- All Linux capabilities dropped and `no-new-privileges` enabled.
- Memory, CPU, PID and wall-clock limits.
- Maximum request size, file count and per-file size.
- Workspace paths cannot escape the disposable workspace.
- Production deployment remains disabled; successful execution is reviewable evidence only.
- `/execute` requires a separate `XP_EXECUTION_APPROVAL_TOKEN` in addition to the API token.

## Request shape
`POST /execute` with a `query` and an `execution` object containing base64-encoded files and a test command.

## Status semantics
- `success`: sandbox process exited zero and evidence was captured.
- `failed`: sandbox started but the test process failed or timed out.
- `blocked`: execution infrastructure is unavailable or approval is absent.

## Explicit boundary
V1 is a controlled execution/testnet layer, not an unattended production deployment system. Successful execution is reviewable evidence only.
