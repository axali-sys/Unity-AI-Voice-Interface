"""Minimal XParallel Testnet v0.1 server."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN", "xparallel-test-token")

KNOWLEDGE = {
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

SERVICES = [
    {"id": "knowledge", "name": "Knowledge Registry", "status": "testnet"},
    {"id": "service-registry", "name": "Service Registry", "status": "testnet"},
    {"id": "agent-router", "name": "Agent Router", "status": "planned"},
]


def send_json(handler, status, payload):
    body = json.dumps(payload, indent=2).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        return self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def do_GET(self):
        # Health checks must work without credentials so hosting platforms can probe the service.
        if self.path == "/health":
            return send_json(self, 200, {"status": "ok", "network": "xparallel-testnet", "version": "0.1"})
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path == "/registry":
            return send_json(self, 200, {"knowledge": list(KNOWLEDGE), "services": SERVICES})
        if self.path.startswith("/knowledge/"):
            key = self.path.split("/knowledge/", 1)[1]
            item = KNOWLEDGE.get(key)
            return send_json(self, 200 if item else 404, item or {"error": "not_found"})
        return send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path != "/ask":
            return send_json(self, 404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return send_json(self, 400, {"error": "invalid_json"})
        query = str(data.get("query", "")).lower()
        if "axaliai" in query:
            answer = KNOWLEDGE["axaliai"]
        elif "xparallel" in query or "mainnet" in query or "ai verse" in query:
            answer = KNOWLEDGE["xparallel"]
        else:
            answer = {"message": "The XParallel testnet has no matching knowledge item yet.", "query": data.get("query")}
        return send_json(self, 200, {"network": "xparallel-testnet", "answer": answer})

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"XParallel Testnet v0.1 listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
