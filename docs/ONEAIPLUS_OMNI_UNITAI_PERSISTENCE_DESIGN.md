# Oneaiplus Persistence Design — Omni and UnitAI

Date: 2026-11-14
Canonical app: Oneaiplus (`c2232890-a16d-4289-b2f8-c8de6365a7b4`)

## Live schema evidence (read-only)

The live database currently exposes these columns:

### projects
- id uuid primary key, default gen_random_uuid()
- user_id uuid not null
- name text not null
- repo text nullable
- status text not null, default planned
- progress integer not null, default 0
- deadline date nullable
- created_at timestamptz not null, default now()

### memories
- id uuid primary key, default gen_random_uuid()
- user_id uuid not null
- title text not null
- body text not null, default empty string
- tags text[] not null, default empty array
- created_at timestamptz not null, default now()

### audit_events
- id uuid primary key, default gen_random_uuid()
- user_id uuid not null
- action text not null
- detail text not null, default empty string
- created_at timestamptz not null, default now()

The live schema matches the checked-in SQL migrations for these three tables. The checked-in `drizzle/schema.ts` is still a blank generated stub and must not be treated as authoritative.

## Proposed persistent workflow data model

Implement only after a reviewed Oneaiplus source branch is available. Do not create tables in the live database as part of this document.

### workflow_plans
- id uuid primary key
- user_id uuid not null
- module text not null, constrained to `omni` or `unitai`
- name text not null (1–200 chars)
- description text not null default ''
- status text not null, constrained to `draft`, `ready_for_review`, `approved`, `archived`
- definition jsonb not null (versioned plan graph; validate at server boundary)
- created_at timestamptz not null default now()
- updated_at timestamptz not null default now()

### workflow_runs
- id uuid primary key
- user_id uuid not null
- plan_id uuid not null references workflow_plans(id) on delete restrict
- status text not null, constrained to `queued`, `blocked`, `running`, `succeeded`, `failed`, `cancelled`
- mode text not null, constrained to `simulation`, `read_only`, `execution`
- input_summary jsonb not null default '{}'
- result_summary jsonb not null default '{}'
- error_code text nullable
- started_at timestamptz nullable
- finished_at timestamptz nullable
- created_at timestamptz not null default now()

## Security and behavior requirements

1. Both tables must enable RLS and have owner policies using `user_id = auth.uid() AND is_oneai_owner()` for authenticated CRUD.
2. `workflow_runs` must additionally be constrained so its `plan_id` belongs to the same `user_id`; enforce with a composite FK or trigger, not UI-only checks.
3. Server functions must call `requireOwner`, validate all input with Zod, and never accept `user_id` from the browser. Set it from authenticated context.
4. Plans are data, not instructions. Workflow definitions must be schema-validated; no arbitrary code, shell commands, SQL, URL fetch, or dynamic imports.
5. Creating, editing, approving or archiving a plan must not execute it.
6. Simulation and read-only modes are the default. `execution` runs remain blocked until a separate, verified XParallel authorization and approval contract exists.
7. Every state transition writes an audit event server-side. Audit rows are append-only for authenticated users.
8. Limit JSON payload sizes and number of steps; add indexes for `(user_id, updated_at DESC)`, `(user_id, created_at DESC)`, and `(plan_id, created_at DESC)`.
9. Use optimistic concurrency (updated_at or version) to prevent silent overwrites.
10. Never persist provider secrets, XP_TOKEN, OAuth tokens, or raw credentials in plan definitions or run summaries.

## UI behavior

- Omni: create/edit/review plans; show validation and dependencies; display run history.
- UnitAI: manage reusable unit/agent definitions and workflow plans; show permissions and execution readiness.
- Clearly distinguish `saved`, `validated`, `approved`, and `executed`. These are not interchangeable states.
- Without a configured model provider, offer deterministic templates and manual editing. Do not claim model-generated output.
- Without a connected XParallel host, show integration as unavailable and keep execution disabled.

## Test requirements

- Owner can create/read/update/archive their plans.
- A different authenticated user cannot read, mutate, or link another owner's plans or runs.
- Browser-supplied user_id is ignored/rejected.
- Invalid module, status, JSON shape, payload size and cross-owner plan references are rejected.
- Plan save/approval does not create a workflow run or invoke external systems.
- Run state transitions are audited.
- Execution mode is blocked absent explicit verified approvals and XParallel credentials held server-side.

## Work completed in this milestone

This document is an implementation specification based on a live read-only schema inspection. No database writes, migrations, source-code changes in the Lovable project, execution, or deployment were performed.
