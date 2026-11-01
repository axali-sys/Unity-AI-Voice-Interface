# XParallel roaming worker

The worker is an outbound polling process. It connects to an existing XParallel API,
registers a runtime, heartbeats, claims queued tasks, executes an allowlisted local
handler, and submits a result with SHA-256 evidence for the canonical JSON input and
output.

## Safety boundary

- No shell execution, dynamic code evaluation, arbitrary plugin loading, or remote code download.
- Initial handlers are deliberately small: `echo` and `text.uppercase`.
- The worker reports hashes as integrity evidence; hashes do not prove that a task was
  truthful or that a remote third party independently audited execution.
- A runtime token is saved locally with owner-only file permissions where supported.
  Keep the token file private and never commit it.
- The owner `XP_TOKEN` is needed only for first registration. Subsequent starts reuse
  the saved runtime token and heartbeat to authenticate.
- `XP_WORKER_PUBLIC_URL` is the HTTPS URL advertised in the runtime registry. The
  current polling worker does not expose an inbound HTTP listener at that address.

## Run locally

Use Python 3.12+ and set:

```bash
export XP_API_URL="https://your-xparallel-api.example"
export XP_TOKEN="your-owner-token" # first registration only
export XP_WORKER_ID="worker-juba-01"
export XP_WORKER_NAME="Juba roaming worker"
export XP_WORKER_PUBLIC_URL="https://worker.example"
python -m xparallel.roaming_worker
```

After the first successful registration, the runtime token is stored in
`.xparallel-worker-token`. Back it up securely; deleting it requires a new
owner-authenticated registration. Do not share or commit it.

## Queue protocol

1. Owner calls `POST /roaming/tasks/dispatch` with runtime_id, task_type and payload.
2. Worker calls `POST /roaming/tasks/claim` with its runtime bearer token.
3. Worker validates task type against its local allowlist and runs the local handler.
4. Worker calls `POST /roaming/tasks/complete` with result and verification hashes.

The worker is not a general-purpose remote computer. Add new task handlers only after
reviewing their input schema, permissions, workspace isolation, timeouts and tests.
