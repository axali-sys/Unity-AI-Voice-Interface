# XParallel V0.1 — Intent-to-Experiment

XParallel V0.1 turns a human goal into a controlled parallel-world experiment.

## Flow

`Human intent -> Intent model -> Sandbox simulation -> Evidence -> Human approval -> Real-world implementation`

V0.1 is deliberately simulation-only. It does **not** execute arbitrary code or automatically modify production systems.

## API

Run from the repository root:

```bash
XP_TOKEN=change-me python xparallel/server.py
```

Health is public:

```text
GET /health
```

The V0.1 experiment endpoint requires the bearer token:

```text
POST /experiment
Authorization: Bearer change-me
Content-Type: application/json

{"query":"Deploy Axaliai V1"}
```

The response records the intent, simulated result, limitations, experiment ID, and whether the result is ready for human review.

## Architecture

- `intent.py` — structured human intent
- `router.py` — intent routing
- `experiment.py` — experiment orchestration
- `simulator.py` — parallel-world simulation boundary
- `permissions.py` — human authority boundary
- `agent.py` — planning-only execution-agent boundary
- `store.py` — knowledge/memory store
- `connectors.py` — constrained HTTPS connector
- `server.py` — HTTP API

The long-term objective is to let XParallel test implementations in a parallel environment and transfer only reviewed, evidence-backed results into the real environment.
