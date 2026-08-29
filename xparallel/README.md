# XParallel V1 — Intent-to-Experiment

XParallel turns a human goal into a controlled parallel-world experiment.

`Human intent -> Intent model -> Sandbox simulation -> Evidence -> Human approval -> Real-world implementation`

V1 adds an explicit controlled Docker execution path while keeping production deployment disabled.

- `intent.py` — structured human intent
- `router.py` — intent routing
- `experiment.py` — experiment orchestration
- `simulator.py` — simulation boundary
- `permissions.py` — human authority boundary
- `v1_runner.py` — controlled project execution
- `server.py` — HTTP API
