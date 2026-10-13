# XParallel Dual Space — Webli Prototype Integration Plan

**Status:** implementation brief / source of truth for the next build step  
**Product:** XParallel Dual Space (Android-first interface, Webli prototype)  
**Canonical repository:** `axali-sys/Unity-AI-Voice-Interface`  
**Relationship:** XParallel is the execution and experimentation infrastructure; Axaliai remains the user-facing gateway. This is not a merger of the two products.

## 1. Product definition

Turn the current Webli-built “XParallel — Dual Account” screen into the **device-facing control surface for the wider XParallel system**. Preserve the useful visual language in the screenshot: dark navy panels, cyan/blue actions, clear space switching, sandbox status, cloned-app cards, storage, and split-view controls.

The screenshot is a prototype UI. Labels such as “Engine v3.5,” “Isolated & Active,” memory usage, and unread counts must only be displayed as live status when the relevant backend/device integration actually reports those values. Otherwise label them as demo/sample data.

## 2. Keep the original XParallel concept intact

XParallel is not only an app cloner. Its core purpose is an isolated parallel environment for building, running, testing, and validating software/AI workflows before any real-world deployment.

The product flow remains:

`Human → Axaliai gateway → XParallel Gateway → Workspace → Sandbox → Test/Experiment → Evidence → Human Approval → Deploy`

- **Axaliai:** front door for an authorized human request; captures intent and presents results.
- **XParallel Gateway:** authenticates requests, validates scope, creates experiments and routes them to isolated workspaces.
- **Workspace:** project files, versions, configuration, logs, and experiment history.
- **Sandbox:** isolated execution environment with explicit resource and network policies.
- **Evidence:** immutable run metadata, test results, logs, artifacts, and provenance.
- **Approval:** a human decision gate before any action affects a real environment.
- **Deploy:** a controlled release step, disabled by default until approval and policy checks pass.

The Dual Space interface is one client of this infrastructure. It should not pretend that an Android app-cloning feature is equivalent to the server-side XParallel execution engine.

## 3. Map the existing screen to the expanded product

### Top status strip
- Product name: **XParallel**
- Connection indicator: Connected / Offline / Needs configuration, derived from an actual health check.
- Resource meter: device storage or sandbox quota only when measured by the relevant API.
- Notifications: actionable experiment, security, or approval events.
- Lock control: lock the local private workspace; never imply it locks remote infrastructure unless confirmed.
- Theme toggle: presentation preference only.

### Space selector
- **Parallel Space:** isolated local profiles / workspaces available on this device.
- **Original Space:** the normal device/app context; do not claim the app can inspect or control it without Android-granted permissions.
- **Parallel Dual View:** a UI layout that compares two permitted workspaces or experiment runs side by side. If Android split-screen cannot be controlled by the app, provide an in-app comparison view instead.

### Action buttons
- **Sandbox Storage:** show per-workspace usage, quota, retention, and delete/export controls.
- **Disguise Icon:** rename/hide only within lawful launcher capabilities and clearly disclose limitations; never use it to impersonate another app or evade security checks.
- **Clone App:** first determine which supported method is available on the device. Prefer Android-supported Work Profile / managed profile / profile mechanisms where applicable. Do not claim arbitrary app cloning is possible on every Android device.
- **Test Parallel Split:** run a harmless diagnostic experiment that records start/end time, environment, status, logs, and evidence. The button must show real progress and a truthful result.

### Workspace / clone cards
Each card should show:
- display name and category;
- state: Not configured / Ready / Running / Failed / Paused;
- last activity and storage only when measured;
- Launch/Open, View Evidence, Pause, and Delete actions;
- confirmation before destructive actions;
- clear distinction between a local Android profile and a remote XParallel experiment.

## 4. V1 architecture and API contract

Use the existing project and existing Axaliai/XParallel integration. Do not create a replacement repository or overwrite unrelated routes/workflows/history.

Suggested API surface (adapt to existing implemented routes rather than duplicating them):

- `GET /health` — service readiness and version.
- `POST /public/ask` — Axaliai intake / explain or plan a request.
- `POST /public/build` — create a proposed build/experiment; return an experiment ID and plan.
- `POST /public/route` — route a validated request to a supported workspace.
- `GET /experiments/{id}` — current state and timestamps.
- `GET /experiments/{id}/evidence` — test summaries, logs, and artifact references.
- `POST /experiments/{id}/approve` — explicit authenticated human approval for the defined action.
- `POST /experiments/{id}/deploy` — permitted only after approval and policy checks.
- Local-device capabilities (profile enumeration, launch, storage) must use a separate Android adapter and explicit OS permissions; do not fake them with server responses.

Keep any existing private `/execute` route private and protected. Never expose `XP_TOKEN`, secrets, raw credentials, or server environment values to client-side Webli code. Do not hardcode credentials in source, browser storage, screenshots, or logs.

## 5. Experiment state machine

Use explicit, persisted states:

`INTAKE → PLAN → SANDBOX → RUNNING → TESTING → EVIDENCE → AWAITING_APPROVAL → APPROVED → DEPLOYING → SUCCEEDED`

Failure/stop paths:
- `FAILED` — capture a safe error summary and evidence.
- `CANCELLED` — user or authorized operator cancelled.
- `REJECTED` — human rejected the proposed release.
- `ROLLED_BACK` — deployment rollback completed and verified.

Only allow valid transitions. A browser button must not directly jump from plan to deploy. Retrying should create a traceable attempt or run revision rather than silently overwrite evidence.

## 6. Security and privacy requirements

- Tenant/user authorization on every remote workspace and experiment.
- Server-side secrets only; rotate credentials if they were ever placed in client code.
- Sandbox resource quotas, execution timeouts, network allowlists/denylists, and restricted filesystem access.
- Separate local Android-profile data from remote experiment data.
- Explicit consent before collecting app metadata, notifications, files, or device diagnostics.
- No credential extraction, bypassing app protections, covert surveillance, or evasion of platform security.
- Audit log for create, run, approve, deploy, delete, and permission changes.
- Redact tokens and personal data from logs.
- Human approval remains mandatory before deployment or any action that affects a real environment.
- Payment/billing stays disabled until explicitly designed and approved.

Android itself enforces per-app sandbox boundaries; app-profile isolation and availability vary by Android version, device manufacturer, and permissions. Do not promise universal cloning or isolation beyond what the platform actually provides.

## 7. Build sequence

### Phase A — connect the prototype honestly
1. Keep the Webli design and current navigation.
2. Add an environment/configuration screen for the XParallel API base URL and connection state.
3. Add a health-check action and display the actual response.
4. Mark all disconnected/sample data clearly.
5. Add a single “Create diagnostic experiment” action that creates an experiment through the existing gateway if configured.

### Phase B — experiment workspace
1. Project/workspace list and create flow.
2. Experiment detail timeline with state, logs, and evidence.
3. Retry/cancel actions with server validation.
4. Approval screen showing exactly what will happen, target environment, diff/artifacts, and risks.
5. Deploy action hidden/disabled until the backend confirms approval and policy checks.

### Phase C — local Android dual space
1. Detect device and Android version capabilities.
2. Implement only platform-supported profile/launch behavior.
3. Request minimum permissions at point of use.
4. Show per-profile state and storage only where APIs provide reliable values.
5. Test install, upgrade, restart, offline, denied permission, low storage, cancellation, and recovery paths.

### Phase D — release readiness
- Unit and integration tests for API state transitions and authorization.
- Test with missing/expired credentials, invalid experiment IDs, denied permissions, offline API, timeouts, and backend failure.
- Verify mobile layout on narrow screens and accessibility labels for controls.
- Build/install a real Android package only after the underlying Android project and signing configuration are available.
- Deploy only from the approved branch/pipeline after checks pass.

## 8. Acceptance criteria

- The app clearly identifies itself as the XParallel Dual Space client.
- It links to the original XParallel project through authenticated gateway calls, not merely shared branding.
- A user can check connectivity, create a diagnostic experiment, view its real state, and inspect evidence.
- UI states never claim a sandbox is active, isolated, or successful without backend/device confirmation.
- Approval is enforced server-side, not only by hiding a button.
- Existing Axaliai gateway routes, XParallel backend, repository history, and workflows are preserved.
- No production deploy occurs automatically as part of this prototype integration.

## 9. Webli implementation prompt

Continue the existing Webli project from its current files and screenshot. Do not start a scratch project and do not replace the existing visual design wholesale.

Build **XParallel Dual Space** as the mobile-first client for the user's original XParallel infrastructure. Keep the dark navy/cyan/blue visual style, Parallel Space / Original Space / Parallel Dual View navigation, Sandbox Storage, Clone App, Test Parallel Split, and workspace cards. Expand it with Projects, Experiments, Evidence, Approvals, and Deployment History.

Connect it to the existing `axali-sys/Unity-AI-Voice-Interface` project and its existing Axaliai-to-XParallel gateway only after reading the repository's actual routes and configuration. Reuse existing endpoints; do not invent working endpoints or silently create a second backend. Keep `XP_TOKEN` and every secret server-side. If the gateway is not configured or reachable, show “Not connected” and provide a setup/diagnostics view rather than fake success.

The canonical workflow is `INTAKE → PLAN → SANDBOX → TEST → EVIDENCE → APPROVAL → DEPLOY`. Create a real diagnostic experiment through the backend when available; show the experiment ID, current state, timestamps, logs, and evidence returned by the service. Enforce human approval for deployment on the server. Keep local Android app/profile capabilities separate from remote software execution and only expose features supported by the actual device and Android permissions.

Preserve all existing project files, routes, workflows, history, and working functionality. Make incremental changes, explain files changed, run available checks, and report blockers honestly. Do not claim the product is operational until an end-to-end test succeeds.
