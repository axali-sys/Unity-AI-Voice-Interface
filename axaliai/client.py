"""Axaliai's first XParallel development-layer client."""
import json
import sys
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8787"
TOKEN = "xparallel-test-token"


def request(path, method="GET", payload=None):
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(
        BASE + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req) as response:
        return json.loads(response.read())


def main():
    query = " ".join(sys.argv[1:]).strip() or "What is XParallel?"
    registry = request("/registry")
    result = request("/ask", "POST", {"query": query})
    print("AXALIAI -> XPARALLEL TESTNET")
    print("Registered knowledge:", ", ".join(registry["knowledge"]))
    print("Registered services:", ", ".join(s["name"] for s in registry["services"]))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
