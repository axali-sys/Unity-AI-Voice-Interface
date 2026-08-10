"""Small JSON knowledge store for XParallel Testnet v0.2."""
import json
import os
from pathlib import Path

DATA_FILE = Path(os.getenv("XP_DATA_FILE", "xparallel/data/knowledge.json"))

DEFAULT = {
    "xparallel": {
        "name": "XParallel",
        "description": "The Parallel AIverse: an AI infrastructure and ecosystem connecting parallel intelligence and infrastructure through X-intersections.",
        "layers": ["intelligence", "infrastructure", "x-link", "applications", "governance"],
    },
    "axaliai": {
        "name": "Axaliai",
        "role": "development and intelligence layer / first XParallel client",
        "website": "https://axaliai.com",
    },
}


def load():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps(DEFAULT, indent=2), encoding="utf-8")
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def get(key):
    return load().get(key)


def search(query):
    q = query.lower()
    results = []
    for key, item in load().items():
        haystack = json.dumps(item).lower()
        if q in key.lower() or q in haystack:
            results.append({"id": key, "data": item})
    return results
