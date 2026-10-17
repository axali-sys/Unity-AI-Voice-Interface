# OneAI release readiness record

**Assessment date:** 2026-10-17  
**Repository:** axali-sys/Unity-AI-Voice-Interface  
**Default branch:** main  
**Candidate branch:** oneai-release-integration  
**Candidate PR:** https://github.com/axali-sys/Unity-AI-Voice-Interface/pull/42
**Tested code commit:** fd2750b120e5cbf86505eb53b9f02b6366a9fe0d
**CI evidence:** [XParallel Integration Tests #24](https://github.com/axali-sys/Unity-AI-Voice-Interface/actions/runs/39070610811) and [Verify Axaliai V1 #115](https://github.com/axali-sys/Unity-AI-Voice-Interface/actions/runs/39070610931) both completed successfully.  
**Release version:** Not assigned; the repository metadata currently declares 0.1.0. Do not publish a release tag until the gates below are cleared.

## Acceptance gates

| Gate | Status | Evidence and remaining work |
|---|---|---|
| A — Application integrity | BLOCKED | Existing routes and previous PRs #5, #20, #22, #26, and #41 are recorded as merged. Candidate changes are on a draft PR. Candidate CI passed Python compilation, inline JavaScript syntax checks, the new Mixer/roaming/chat integration tests, and the existing V1/memory/planner/conversation test suites. Live endpoint smoke tests are still missing. |
| B — AI operation | BLOCKED | A configurable provider-neutral Mixer and telemetry contract are implemented on the candidate branch. No provider credentials or live provider calls have been verified. Configure XP_MIXER_MODELS_JSON and the matching server-side keys; run real provider tests and inspect returned model IDs, usage, hashes, and errors. |
| C — Roaming operation | BLOCKED | Candidate supports Tavily retrieval and allowlisted HTTPS workers. No TAVILY_API_KEY or trusted worker has been verified. Worker entries are configuration-backed and marked unprobed; persistent discovery, health probes, circuit breakers, retries, and durable distributed task state remain incomplete. |
| D — XParallel operation | BLOCKED | Existing bounded Docker experiment and approval flow remain in the default branch. Sandbox execution and approval tests have not been executed in this assessment. Verify Docker availability, resource limits, logs, cleanup, and explicit approval against the intended host. |
| E — Voice operation | BLOCKED | Browser speech recognition and speech synthesis are present in the current interface. A complete live interaction has not been tested on Android or desktop, and browser support varies. |
| F — Persistence and security | BLOCKED | SQLite-backed conversation and memory modules exist, but production durability and per-user isolation require deployment-level verification. Current workspace selection must not be treated as an authenticated identity boundary. Add authenticated principal-to-workspace binding, durable database storage, retention/deletion checks, and network egress enforcement before multi-user production. |
| G — Deployment | BLOCKED | The connected Vercel API returned HTTP 403 for the selected scope. Repository status checks also show Vercel deployment-rate-limit failures. Live website and backend endpoints could not be verified. No deployment is claimed. |
| H — Distribution | BLOCKED | No verified production URL, native Android package, signed release artifact, or public release approval is available. Documentation and configuration examples are in progress. |

## Candidate changes

- Configurable OpenAI, Anthropic, Google Gemini, and Moonshot provider adapters.
- Explicit model IDs supplied by the operator instead of guessed defaults.
- Provider-call evidence: provider/model, status, latency, provider-reported token counts, response hash, and skipped reasons.
- Authenticated retrieval-only roaming endpoint with Tavily and operator-allowlisted workers.
- OneAI branding, roaming mode, service configuration status, and visible Mixer evidence in the existing interface.
- Added Mixer and roaming unit tests and extended the existing integration workflow to run them.

## Release notes draft

**Added**
- OneAI chat now routes through the shared Mixer when the candidate is deployed and configured.
- Internet roaming can use a configured search provider and trusted independent worker endpoints.
- The interface can display actual Mixer call evidence and roaming configuration status.

**Security and reliability**
- Provider model IDs must be explicitly configured.
- API keys remain server-side.
- Roaming requires bearer-token authorization and exact worker-host allowlisting.
- Redirects are rejected for configured worker requests; public-address DNS checks are defense-in-depth and do not replace network egress controls.
- Retrieval is explicitly separated from execution; external actions remain approval-gated.

**Known limitations**
- No live provider calls, roaming calls, voice interactions, sandbox executions, or production deployment have been verified in this release assessment.
- Distributed worker health, circuit breakers, durable task coordination, and production-grade network egress enforcement are incomplete.
- UnitAI identity, biometric, GPS whitelist, and Ethereum audit integrations must remain marked unconfigured until verified.
- No APK or store release is claimed.

## Configuration checklist

- [ ] Configure XP_TOKEN and XP_EXECUTION_APPROVAL_TOKEN securely.
- [ ] Configure XP_MIXER_MODELS_JSON using currently enabled provider model IDs.
- [ ] Add only the provider API keys needed for the intended launch.
- [ ] Configure TAVILY_API_KEY if live web search is required.
- [ ] If workers are used, configure ONEAI_ROAMING_WORKERS and ONEAI_ROAMING_ALLOWED_HOSTS; restrict outbound traffic at the host/network layer.
- [ ] Configure XP_MEMORY_DB on durable, backed-up storage and bind authenticated users to isolated workspace IDs.
- [ ] Set XP_PUBLIC_ORIGINS to the exact production frontend origin.
- [ ] Confirm the backend host has Docker available and the sandbox resource limits are enforced.
- [ ] Reauthorize the Vercel integration for the correct account/team and resolve deployment-rate-limit restrictions.
- [ ] Run the full GitHub Actions test suite and inspect its logs.
- [ ] Run authenticated smoke tests and one live provider call in a controlled environment.
- [ ] Test voice and layout at Android mobile and desktop viewport sizes.
- [ ] Publish privacy, terms, support, and retention information before public launch.

## Rollback plan

1. Keep the candidate isolated until CI, security review, and a live staging smoke test pass.
2. If a deployment fails, promote the last known-good deployment using the existing host's rollback controls; do not rewrite Git history.
3. Disable provider calls by removing the affected provider from XP_MIXER_MODELS_JSON or removing its server-side key.
4. Disable roaming by removing TAVILY_API_KEY and worker configuration; retain explicit unavailable responses.
5. Disable real execution by withholding execution credentials and approval tokens.
6. Preserve logs and test evidence, then fix forward in a reviewable pull request.

## Test evidence policy

Mocked tests validate code paths only. They do not prove a live provider, worker, voice service, sandbox, or deployment is operational. A gate must not be marked PASS until its actual test command or live verification result is recorded.
