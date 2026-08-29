# Axaliai → XParallel → isolated deployment experiment

This is the first concrete software-development vertical slice.

```text
Human
  ↓
axaliai.com
  ↓
"Deploy this project"
  ↓
XParallel
  ↓
Create isolated sandbox
  ↓
Run implementation
  ↓
Test / observe
  ↓
SUCCESS or FAILURE
  ↓
Explain what happened
  ↓
Human approves
  ↓
Real environment
```

## V0.1 boundary

The real-world deployment step remains outside the experiment runner. A successful experiment produces evidence and a transfer proposal; it does not deploy automatically.

## Sandbox

When Docker is available, `xparallel/docker_runner.py` runs a repository-provided command inside a constrained container with no network, a read-only container root, dropped Linux capabilities, `no-new-privileges`, PID/CPU/memory limits, and a temporary writable workspace. If Docker is unavailable, the existing deterministic simulator remains the safe fallback.

## Example task

A future Axaliai request can be represented as:

`Deploy this project`

XParallel should resolve the project, select an approved build/test command, run it in the isolated environment, capture stdout/stderr/exit status, and return an evidence record. The transfer layer then presents the result for human approval before any real deployment integration is enabled.
