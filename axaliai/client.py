"""Axaliai's first XParallel development-layer client."""
import json
import os
import sys
from urllib.request import Request, urlopen

BASE = os.getenv("XP_URL", "http://127.0.0.1:8787").rstrip("/")
TOKEN = os.getenv("XP_TOKEN", "xparallel-test-token")


def request(path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(
        BASE + path,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=15) as response:
        return json.loads(response.read())


def main():
    query = " ".join(sys.argv[1:]).strip() or "What is XParallel?"
    registry = request("/registry")
    result = request("/ask", "POST", {"query": query})
    print("AXALIAI -> XPARALLEL TESTNET v0.2")
    print("Endpoint:", BASE)
    print("Knowledge:", ", ".join(registry["knowledge"]))
    print("Services:", ", ".join(s["name"] for s in registry["services"]))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
