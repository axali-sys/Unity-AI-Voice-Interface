# AxaliAI Roaming AI integration

AxaliAI Roaming is an opt-in multi-agent planning layer wired into the existing XParallel `/world/plan` endpoint. It intentionally reuses the repository's configured provider, workspace-scoped memory vault, and knowledge router rather than introducing a second server or replacing existing routes.

## Enable

Set the environment variable:

```env
XP_ROAMING_ENABLED=1
```

Leave it unset or set it to `0` to preserve the original XParallel parallel-world planner. The existing `XP_AI_API_KEY`, `XP_AI_CHAT_COMPLETIONS_URL`, and `XP_AI_MODEL` settings remain the provider configuration source.

## Flow and safety boundaries

1. **Planner** creates a bounded task plan.
2. **Read-only evidence gathering** calls the existing local knowledge router and workspace-scoped memory search.
3. **Researcher** reviews the plan and bounded evidence, distinguishing facts, assumptions, and unknowns.
4. **Arbiter** reconciles the analysis and produces the final recommendation.
5. The response includes agent model labels, latency, SHA-256 response hashes, stage checkpoints, evidence counts, and an explicit human-approval gate.

The endpoint proposes; it does not execute arbitrary code, make outbound tool calls, or change real-world systems. Execution continues to use the existing XParallel approval controls. The three agents use the same configured provider; this is not yet a cross-vendor AI Mixer.

## Request

Use the existing authenticated endpoint:

```http
POST /world/plan
Authorization: Bearer <XP_TOKEN>
Content-Type: application/json

{
  "query": "Investigate why the service health check is failing",
  "workspace_id": "default"
}
```

The response preserves the existing `{ "plan": ... }` envelope and adds a `plan.roaming` object containing the multi-agent evidence.

## Verification

Run the repository's existing test suite plus the new focused tests:

```bash
python -m unittest discover -s tests -p 'test_roaming_ai.py'
python -m unittest discover -s tests
```

The tests use mocked provider and retrieval responses; they do not prove live model credentials, hosting configuration, or production deployment. Configure the flag in a preview environment first and compare the original planner with the roaming output before enabling it in production.
