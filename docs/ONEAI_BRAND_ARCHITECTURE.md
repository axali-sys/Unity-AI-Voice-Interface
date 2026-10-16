# OneAI brand and module architecture

## Brand decision
OneAI is the unified public-facing brand formed by combining Axaliai and UnityAI. Existing historical names remain in source history, credits, and legacy records where needed; they are not separate top-level product identities in the new user experience.

## Product architecture
- **OneAI** — unified identity, user interface, account experience, and entry point.
- **Parallel Intelligence / AI Mixer** — orchestration across explicitly configured AI providers. Provider calls, model IDs, latency, token usage, response hashes, errors, and skipped-provider reasons must be reported truthfully.
- **Jellybox** — tokenization/context budgeting and memory retrieval, summarization, and persistence.
- **UIDaaS** — identity, authentication, authorization, scoped credentials, and audit records.
- **Omni** — intelligence orchestration and task coordination, integrated with the AI Mixer.
- **XParallel** — distinct isolated build/test/execution infrastructure, with human approval required for real execution.

## Product boundaries
OneAI unifies the experience, not every service into one undifferentiated module. Keep Jellybox, UIDaaS, Omni, the AI Mixer, and XParallel as independently testable components with clear contracts. Keep existing routes, history, and workflows intact.

## Rollout and acceptance
1. Apply OneAI naming to user-facing interface copy and metadata.
2. Preserve backend/API compatibility and historical attribution.
3. Test responsive UI, search and command behavior, existing API routes, auth controls, and approval-gated execution.
4. Verify configured live AI providers separately from mocked/unit tests.
5. Deploy only after checks pass; do not describe a commit or preview as a verified production deployment.
