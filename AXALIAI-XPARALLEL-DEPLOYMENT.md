# Axaliai + XParallel unified deployment

## Release

**XParallel Testnet 0.4.0** is the unified release containing the currently required prototype layers:

1. `xparallel/server.py` — API/runtime
2. `xparallel/store.py` — knowledge registry
3. `xparallel/router.py` — Ask/Understand/Build routing
4. `xparallel/connectors.py` — controlled HTTPS source retrieval
5. `axaliai/client.py` — CLI client
6. `axaliai/gateway.py` — Axaliai gateway facade
7. `Dockerfile` / `Procfile` / `render.yaml` — deployment startup

## Deployment contract

Set these environment variables on the host:

- `XP_TOKEN` — required deployment bearer token
- `XP_HOST=0.0.0.0`
- `PORT` — supplied by the hosting provider
- `XP_URL` — the public XParallel URL when running the Axaliai client separately

Never commit a production `XP_TOKEN`.

## Start

The deployment host should run:

```bash
python xparallel/server.py
```

Or use the included Docker image:

```bash
docker build -t xparallel-testnet .
docker run -p 8787:8787 -e XP_TOKEN=replace-me xparallel-testnet
```

## Axaliai gateway

After XParallel is deployed, configure the Axaliai runtime with:

```text
XP_URL=https://YOUR-XPARALLEL-HOST
XP_TOKEN=YOUR_DEPLOYMENT_TOKEN
```

Then Axaliai can call the unified XParallel layer through `axaliai/gateway.py`.

## What this release is

This is a **testnet/prototype**, not a production mainnet. External retrieval is limited to explicitly supplied HTTPS URLs. Production requirements still include a real identity provider, scoped authorization, TLS, rate limiting, secret rotation, persistent production storage, audit logging, and an approved AI/model integration.

## Target architecture

```text
                    axaliai.com
                         |
                  Axaliai Gateway
                         |
               Authentication / Policy
                         |
                  XParallel API
                         |
       +-----------------+-----------------+
       |                 |                 |
   Knowledge          Router          Connectors
     Store                              HTTPS
       |                 |                 |
       +-----------------+-----------------+
                         |
                    AI / Agents
                         |
                 XParallel AIverse
```
