# XParallel Testnet v0.1

XParallel is the Parallel AIverse infrastructure prototype. This directory contains the first test environment used by Axaliai as its development-layer client.

## Architecture

```text
User -> Axaliai client -> XParallel API -> Registry / Knowledge / Services
                                      |
                               Auth + Permissions
```

The prototype uses a dependency-free Python HTTP service so the architecture can be tested before introducing production infrastructure.

## Automatic deployment

The repository includes a `Procfile` and `render.yaml`. A compatible Python web host can start XParallel with:

```bash
python xparallel/server.py
```

The server binds to `0.0.0.0` and reads the hosting platform's `PORT` environment variable. Set `XP_TOKEN` as a deployment secret; do not commit a production token.

The public health endpoint is:

```text
GET /health
```

It does not require authentication so deployment platforms can monitor the service.

## Local run

```bash
python xparallel/server.py
```

Default local address: `http://127.0.0.1:8787`.

## Test through Axaliai

Set the XParallel endpoint and token if the server is remote:

```bash
export XP_URL=https://YOUR-XPARALLEL-HOST
export XP_TOKEN=YOUR_TEST_TOKEN
python axaliai/client.py "What is XParallel?"
```

The client discovers the registry, retrieves knowledge, and returns an Axaliai-style answer.

## Security

This is a testnet. Authentication is a bearer token for the prototype. Production deployment should replace it with proper identity, key rotation, authorization scopes, TLS, rate limits, and audit logging.
