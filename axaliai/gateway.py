"""Minimal Axaliai gateway facade for the unified XParallel testnet."""
import json
import os
from urllib.request import Request, urlopen

XP_URL = os.getenv("XP_URL", "http://127.0.0.1:8787").rstrip("/")
XP_TOKEN = os.getenv("XP_TOKEN", "xparallel-test-token")


def xparallel(path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(
        XP_URL + path,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {XP_TOKEN}", "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read())


def ask(query):
    return xparallel("/ask", "POST", {"query": query})


def build(query):
    return xparallel("/build", "POST", {"query": query})


def health():
    return xparallel("/health")
