"""XParallel v0.3 intent router."""
from .store import search


def route(query: str) -> dict:
    q = query.lower()
    if any(word in q for word in ("build", "create", "develop", "make")):
        mode = "build"
    elif any(word in q for word in ("compare", "explain", "how", "why", "summarize")):
        mode = "understand"
    else:
        mode = "ask"
    return {"mode": mode, "resources": search(query)}
