# OneAI Hybrid Free Access Hub — implementation note

## Goal
Route tasks across local open-source models and legitimate free cloud tiers,
while keeping paid provider calls disabled unless explicitly enabled and
approved. This is an additive first slice for the existing OneAI/XParallel
repository; it does not replace the current router or frontend.

## Initial routing policy
1. Prefer a configured, verified-available local provider.
2. Fall back to a configured, verified-available free cloud provider.
3. Consider a paid provider only when paid routing is enabled and explicit
   approval is granted.
4. Treat unknown availability/quota as unknown, never as free or available.
5. If no eligible provider exists, report the limitation; do not bypass login,
   paywalls, licence checks, quotas, or provider access controls.

## Hybrid runtime
Ollama is the first candidate for optional local inference on a compatible
computer. Local inference has no per-request API charge, but still requires
hardware, electricity, storage, and model downloads. The browser/mobile client
must not be expected to host large models. Provider adapters and live quota
checks are future integration tasks.

## Security and verification
- Provider directory records contain metadata only; never store API secrets in
  this directory or return them to the browser.
- Live status must be supplied by a real health/quota probe before routing.
- Keep paid routing disabled by default.
- Add audit events for routing decisions without logging prompts or secrets
  unnecessarily.
- Add per-workspace isolation before persisting provider preferences.
- No production deployment is part of this change.

## Scope of this first slice
The xparallel/free_access_hub.py module provides a deterministic, unit-testable
policy layer. It is not yet wired into xparallel/server.py, the Next.js API,
Ollama, or any live provider. Integration requires inspecting the server's
existing request/auth/error contracts and testing end-to-end before enabling it.
