"""Independent provider panel for Parallel Intelligence.

Calls only explicitly configured HTTPS OpenAI-compatible endpoints. Each
provider receives the same bounded research question independently. This
module reports agreement signals, not factual consensus or verification.
"""
from __future__ import annotations
import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


def _provider_slots():
    slots = []
    primary = {
        "id": os.getenv("XP_AI_PROVIDER_ID", "primary").strip(),
        "endpoint": os.getenv("XP_AI_CHAT_COMPLETIONS_URL", "https://api.openai.com/v1/chat/completions").strip(),
        "key": os.getenv("XP_AI_API_KEY", "").strip(),
        "model": os.getenv("XP_AI_MODEL", "gpt-4o-mini").strip(),
    }
    secondary = {
        "id": os.getenv("XP_AI_SECONDARY_PROVIDER_ID", "secondary").strip(),
        "endpoint": os.getenv("XP_AI_SECONDARY_CHAT_COMPLETIONS_URL", "").strip(),
        "key": os.getenv("XP_AI_SECONDARY_API_KEY", "").strip(),
        "model": os.getenv("XP_AI_SECONDARY_MODEL", "").strip(),
    }
    for slot in (primary, secondary):
        if slot["endpoint"] and slot["key"] and slot["model"] and slot["endpoint"].startswith("https://"):
            slots.append(slot)
    return slots


def capability_status():
    slots = _provider_slots()
    return {
        "configured_provider_count": len(slots),
        "providers": [{"id": p["id"], "model": p["model"]} for p in slots],
        "multi_model_consensus_available": False,
        "independent_panel_available": len(slots) >= 2,
        "reason": ("Two independently configured HTTPS model endpoints are ready for a panel run."
                   if len(slots) >= 2 else
                   "Configure a second HTTPS OpenAI-compatible provider endpoint, model and key to enable independent panel runs."),
    }


def _invoke(provider, query):
    system = (
        "You are one independent analyst in a multi-model research panel. "
        "Analyze the question independently. State assumptions, key findings, "
        "uncertainties and evidence needed. Do not claim external verification."
    )
    body = json.dumps({
        "model": provider["model"],
        "temperature": 0.2,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": query}],
    }).encode("utf-8")
    request = Request(provider["endpoint"], data=body, method="POST", headers={
        "Authorization": "Bearer " + provider["key"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    try:
        with urlopen(request, timeout=35) as response:
            payload = json.loads(response.read(1_000_000).decode("utf-8"))
        answer = payload["choices"][0]["message"]["content"]
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("parallel_provider_request_failed:" + provider["id"]) from exc
    if not isinstance(answer, str) or not answer.strip():
        raise RuntimeError("parallel_provider_empty_response:" + provider["id"])
    return {"provider_id": provider["id"], "model": provider["model"],
            "response": answer.strip()[:12000], "status": "completed"}


def research(query, workspace_id="default"):
    query = str(query or "").strip()
    if not query:
        raise ValueError("query_required")
    if len(query) > 4000:
        raise ValueError("query_too_large")
    slots = _provider_slots()
    if len(slots) < 2:
        return {
            "mode": "single_provider_plan",
            "collaboration_status": "not_available",
            "capability_status": capability_status(),
            "execution_performed": False,
            "verified": False,
            "reason": "Two configured providers are required; no simulated panel was created.",
        }
    # Independent requests; do not present partial output as a completed panel.
    responses = [_invoke(provider, query) for provider in slots]
    return {
        "mode": "independent_multi_model_panel",
        "collaboration_status": "responses_collected_not_consensus",
        "workspace_id": workspace_id,
        "capability_status": capability_status(),
        "responses": responses,
        "comparison": {
            "response_count": len(responses),
            "comparison_status": "human_or_evaluator_review_required",
            "consensus_claimed": False,
            "verification_performed": False,
        },
        "execution_performed": False,
        "verified": False,
    }
