# XParallel Security Research V1

Controlled, authorized security-research harness for Axaliai/XParallel.

## Safety boundary

- Synthetic data only by default.
- No third-party accounts or private data.
- No credential exfiltration.
- No persistence, disruption, mass enumeration, or automatic exploit escalation.
- Stop immediately when an authorization or privacy boundary is crossed.
- OpenAI production testing is permitted only where explicitly authorized and in scope under the applicable OpenAI security/safety program.

## Tests

- AX-OPENAI-001: authorization boundary
- AX-OPENAI-002: synthetic-secret prompt-injection observation
- AX-OPENAI-003: agent action boundary
- AX-OPENAI-004: evidence/reporting workflow

## Run

```bash
python -m runner.runner
```

The default runner is local and uses synthetic fixtures. It does not send requests to OpenAI or any third-party service.
