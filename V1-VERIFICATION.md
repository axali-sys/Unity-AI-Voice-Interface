# Axaliai V1 Verification Gate

## Goal

Establish a reproducible, evidence-based release gate for Axaliai/XParallel.

## Required gates

1. Python sources compile successfully.
2. Automated tests pass in GitHub Actions.
3. `/health` returns HTTP 200 with the expected network/version contract.
4. Deployment environment provides `XP_TOKEN` and a platform-assigned `PORT`.
5. Render deployment is confirmed externally by a successful health check.
6. `https://axaliai.com/` is confirmed to route to the intended service.
7. Any blockchain anchoring is treated separately and is not considered complete merely because CI/CD deployment succeeds.

## Current status

- Repository implementation: present.
- Verification workflow: added.
- Runtime dependency manifest: added.
- Live production availability: **not yet independently verified**.
- Blockchain anchoring: **not implemented by the deployment manifest**.

Do not label the application production-ready until gates 1–6 have evidence.
