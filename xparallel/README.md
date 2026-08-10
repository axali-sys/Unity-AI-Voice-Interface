# XParallel Testnet v0.1

XParallel is the Parallel AIverse infrastructure prototype. This directory contains the first local test environment used by Axaliai as its development-layer client.

## Architecture

```text
User -> Axaliai client -> XParallel API -> Registry / Knowledge / Services
                                      |
                               Auth + Permissions
```

The prototype deliberately uses a small, dependency-free Python HTTP service so the architecture can be tested before introducing production infrastructure.

## Run

```bash
python xparallel/server.py
```

The test server listens on `http://127.0.0.1:8787`.

## Test through Axaliai

In another terminal:

```bash
python axaliai/client.py "What is XParallel?"
```

The client authenticates with the test token, discovers the registry, retrieves knowledge, and returns an Axaliai-style answer.

## Security

This is a local testnet only. The token in the client is a development credential and must be replaced by real authentication before deployment.
