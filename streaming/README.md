# Stream Axaliai at Unity Technologies

This package defines the production streaming-host layer for Axaliai/XParallel.

## Runtime

`streaming/stream_host.py` provides:

- `GET /health` for hosting health checks.
- `GET /stream?query=...` for Server-Sent Events (SSE).
- `XP_TOKEN` authentication without committing credentials.
- `XP_NETWORK=xparallel-mainnet` as the production network identifier.
- `STREAM_BRAND="Stream Axaliai at Unity Technologies"` as the service identity.

## Production

The host is designed to run behind HTTPS on the Axaliai domain. The Windows executable is built by GitHub Actions; the hosted service remains the canonical server process.

This is a streaming transport/hosting layer. It does not claim that Unity Technologies operates or endorses Axaliai; the brand string is a project label.
