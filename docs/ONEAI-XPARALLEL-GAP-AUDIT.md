# OneAI / XParallel Current-State Audit and Gap Register

**Audit date:** 2026-10-27  
**Repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Scope:** GitHub branch/PR metadata and selected source/docs inspected through GitHub. No local test run, live endpoint call, provider call, or deployment action was performed as part of this audit.

## Executive result

The repository contains substantial existing XParallel and OneAI work. The safest path is to continue that work—not replace it with a starter project. The Parallel Verse candidate is real code on a development branch, but it is not the same as a fully deployed autonomous digital world. UIDaaS and Jellybox are presently best treated as architecture concepts requiring implementation/verification, while Omni orchestration has existing related modules but needs an explicit run lifecycle and end-to-end evidence before its full proposed role can be claimed.

## Evidence inspected

- Main branch `README.md` describes a polished assistant UI and an XParallel API proxy with local demo fallback when no backend is configured.
- Main branch `package.json` lists Next.js 14, React 18, and Vercel Analytics.
- Open draft PR #44, **Add XParallel Parallel Verse foundation and verification tests**, targets `main` from `xparallel-parallel-verse-verify`, head `8a363e06948ecb76e3c729c224741ab690ea55b9`. It reports passing CI workflows for the listed tests, while explicitly warning that this is not live production, provider, or cross-instance persistence verification.
- Open draft PR #45, **Add independent local-first OneAI assistant**, targets `oneai-combined-verify` from `oneai-independent-assistant`, head `fa6697fdb11bd7c21fe51cec8c7799869f59304a`. It adds an Ollama-backed path but requires a reachable Ollama service and downloaded model for live inference.
- Open draft PR #42, **Integrate OneAI AI Mixer, roaming retrieval, and workspace evidence**, remains a draft and documents provider/roaming configuration and production hardening gaps.
- PR #43, **Add OneAI responsive workspace foundation**, is marked merged in GitHub metadata. Its description lists OneAI workspace navigation and initial Parallel Verse primitives; its verification note says the tests had not yet been executed at that time.
- The current Parallel Verse docs describe agent registration, spaces, append-only events, and task records; the API docs warn that workspace IDs are client-supplied and auth uses a shared bearer token.
- The SQLite store explicitly uses `/tmp` as a serverless fallback, which is ephemeral. PostgreSQL support is opt-in and requires migrations and a separately configured database.

## Component status matrix

| Component | Evidence in repository | Current honest status | Main gap |
|---|---|---|---|
| OneAI workspace | Responsive workspace UI and navigation reported in merged PR #43; main README describes assistant UI | Partially implemented; verify current main/preview behavior | Run full UI and API-route tests against current candidate |
| XParallel gateway | Existing server/router/auth/execution modules and public endpoint contracts | Implemented code exists; live status must be tested | Verify deployed auth, health, provider calls, routing, and approval gate |
| Parallel Verse | SQLite/PostgreSQL adapters, API routes, tests, SQL migrations in draft PR #44 | Development foundation; draft PR not merged | Identity-bound tenancy, durable storage, real scheduler/runtime |
| Omni | Existing planner/router and orchestration-related modules | Related orchestration code exists; complete lifecycle not established by this inspection | Persisted run/step state, bounded retries, approvals, evidence and cancellation |
| UIDaaS | No UIDaaS implementation was confirmed by the inspected source paths | Concept/architecture requirement | Proven auth/session lifecycle, device trust, server-side identity-to-workspace mapping |
| Jellybox | No SmartBlock/artifact execution subsystem was confirmed by the inspected source paths | Concept/architecture requirement | Typed/versioned SmartBlocks, integrity hashes, artifact store, sandbox and rollback |
| AI Mixer | Draft PR #42 documents provider-neutral adapters and evidence metadata | Candidate implementation on an unmerged branch | Merge/rebase review, configure keys, live provider calls and failure-path checks |
| Local-first assistant | Draft PR #45 adds Ollama path according to PR description | Candidate implementation on an unmerged branch | Verify code/CI and actual reachable local inference endpoint |
| Durable memory | SQLite defaults and optional PostgreSQL adapters are documented | Local persistence code exists; production durability not proven | Durable mounted volume/DB, restart test, backup/restore and tenant isolation |
| Production deployment | Existing deployment metadata/URLs from project context; not live-tested in this audit | Not verified here | Live endpoint checks, environment/secret review, CI and explicit release approval |

## Branch and merge risk

GitHub compare metadata shows `xparallel-parallel-verse-verify` is **diverged** from `main`: 35 commits ahead, 5 behind, with merge base `c4ec7d8aa0d0f39b2eace587f2f4f94a307c4f12`. `oneai-independent-assistant` is also diverged from `main`: 34 commits ahead, 5 behind. These branches must not be merged blindly or assumed to include one another. Review the exact PR diffs, reconcile the shared `xparallel/server.py`, `xparallel/chat_service.py`, frontend entry point, requirements, and tests, then run CI on a unified candidate branch.

## Prioritized next actions

### P0 — Preserve and verify
1. Keep `main` unchanged until a combined candidate is reviewed.
2. Fetch current branch heads and review PR #44, #45, and #42 diffs, including conflicting server/frontend changes.
3. Rebase/merge into a new integration branch only after checking branch ancestry and preserving Git history.
4. Run all Python tests and frontend build/tests on the exact integration commit; save CI run IDs and results.

### P1 — Security before multi-user exposure
1. Replace client-authoritative workspace IDs with identity-derived membership.
2. Add tests for unauthenticated, expired/revoked, wrong-role, cross-workspace read, and cross-workspace write attempts.
3. Ensure every private route checks authorization and all secrets stay server-side.
4. Keep execution disabled unless the established approval mechanism passes.

### P1 — Persistence and real provider evidence
1. Keep SQLite as default for $0 development.
2. Never treat serverless `/tmp` as durable production memory.
3. Use a disposable PostgreSQL database only if one is already available or its cost is explicitly approved; do not create a paid service under the current $0/month budget.
4. Test save -> process restart -> retrieve, workspace isolation, and backup/restore.
5. Run one real provider call only after valid server-side credentials are configured; record provider/model, latency, status, and failure behavior without exposing secrets.

### P2 — UIDaaS, Jellybox, and Omni
1. Implement UIDaaS identity/session/workspace contracts on a proven auth foundation.
2. Add Jellybox artifact/SmartBlock schemas and content hashing before any execution feature.
3. Add Omni's persisted run/step state machine and evidence bundle.
4. Connect these to Parallel Verse via authenticated events/tasks, not by bypassing its access boundary.
5. Consider distributed device nodes or consensus only after identity, trust, threat modeling, and economic costs are documented.

## Acceptance checklist for the first integrated milestone

- [ ] OneAI UI routes to Assistant, AI Mixer, Build Studio, Repair Shop, Omni, Jellybox, UIDaaS, and XParallel portal without broken links.
- [ ] UI capability states match actual server configuration.
- [ ] Parallel Verse agent/space/event/task CRUD passes tests, including restart and cross-workspace rejection.
- [ ] Authenticated identity—not request body—determines workspace access.
- [ ] A task record is not misrepresented as a running job.
- [ ] At least one configured model provider returns a real response and reports failures honestly.
- [ ] No browser-visible provider key, XP token, database URL, or execution approval token.
- [ ] Exact candidate CI passes; preview smoke tests pass; production remains untouched until explicitly approved.

## Scope boundary

This audit is read-only evidence about repository metadata and selected files. It does not certify security, current deployment health, real AI inference, or production readiness. No production deployment or merge is authorized by this document.
