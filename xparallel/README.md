# XParallel V1 — Intent-to-Experiment

XParallel V1 turns a human goal into a controlled parallel-world experiment and, when explicitly approved, a bounded Docker project test.

## Flow

`Human intent -> Intent model -> Sandbox simulation / controlled project execution -> Evidence -> Human approval -> Real-world implementation`

Production deployment remains outside the V1 execution boundary.

## API

Run from the repository root:

```bash
XP_TOKEN=change-me python xparallel/server.py
```

Health is public:

```text
GET /health
```

The authenticated experiment endpoint accepts an intent and optional project workspace:

```text
POST /experiment
Authorization: Bearer change-me
Content-Type: application/json

{"query":"Deploy Axaliai V1","execution":{"files":{"test_hello.py":"<base64>"},"test_command":"python -m unittest discover -v"}}
```

`POST /execute` uses the same controlled execution path but additionally requires `X-XParallel-Approval` matching `XP_EXECUTION_APPROVAL_TOKEN`.

## V1 controls

- Docker-only project execution; the host never evaluates the supplied test command.
- No container network access.
- Read-only container root filesystem with a disposable writable workspace.
- Linux capabilities dropped and `no-new-privileges` enabled.
- Memory, CPU, PID and wall-clock limits.
- File count, file size, and request size limits.
- Workspace paths cannot escape the disposable workspace.
- Successful execution produces reviewable evidence only; production deployment is disabled.

## Architecture

- `intent.py` — structured human intent
- `router.py` — intent routing
- `experiment.py` — experiment orchestration
- `simulator.py` — parallel-world simulation boundary
- `permissions.py` — human authority boundary
- `agent.py` — planning-only execution-agent boundary
- `store.py` — knowledge/memory store
- `connectors.py` — constrained HTTPS connector
- `docker_runner.py` — fixed Docker probe
- `v1_runner.py` — controlled project execution
- `server.py` — HTTP API

The long-term objective is to let XParallel test implementations in a parallel environment and transfer only reviewed, evidence-backed results into the real environment.
