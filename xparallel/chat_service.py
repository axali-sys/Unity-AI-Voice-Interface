"""Authenticated provider-backed chat through the shared OneAI AI Mixer."""
from __future__ import annotations

import asyncio
from typing import Any

from .memory_vault import search_memories
from .mixer import mix

def chat(messages: list[dict[str, str]], workspace_id: str = "default", use_memory: bool = True) -> dict[str, Any]:
    if not isinstance(messages, list) or not messages or len(messages) > 20:
        raise ValueError("messages_required_or_too_many")
    bounded = []
    for item in messages:
        if not isinstance(item, dict) or item.get("role") not in {"user", "assistant"} or not isinstance(item.get("content"), str):
            raise ValueError("invalid_message")
        content = item["content"].strip()
        if not content or len(content) > 12000:
            raise ValueError("invalid_message_content")
        bounded.append({"role": item["role"], "content": content})
    if bounded[-1]["role"] != "user":
        raise ValueError("last_message_must_be_user")

    memory_sources = []
    if use_memory:
        for item in search_memories(bounded[-1]["content"], workspace_id, limit=3):
            memory_sources.append({
                "id": item.get("id"),
                "summary": str(item.get("summary", ""))[:300],
                "content": str(item.get("content", ""))[:1600],
            })
    conversation = "\n".join(
        ("User: " if item["role"] == "user" else "Assistant: ") + item["content"]
        for item in bounded
    )
    memory_context = "\n\n".join(
        f"[Memory {item['id']}] {item['summary']}\n{item['content']}" for item in memory_sources
    )
    result = asyncio.run(mix(conversation, memory_context))
    answer = str(result.get("final_answer", "")).strip()
    model = (result.get("synthesizer") or {}).get("model_id")
    if not model:
        successful = next((call for call in result.get("calls", []) if call.get("status") == "success"), {})
        model = successful.get("model_id", "unavailable")
    return {
        "answer": answer,
        "model": model,
        "mixer": result,
        "memory_sources": [{"id": x["id"], "summary": x["summary"]} for x in memory_sources],
    }
