"""XParallel Testnet v0.2 API."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

from store import get, load, search

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN", "xparallel-test-token")

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
        if self.path == "/health":
            return send_json(self, 200, {"status": "ok", "network": "xparallel-testnet", "version": "0.2"})
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path == "/registry":
            data = load()
            return send_json(self, 200, {"knowledge": list(data), "services": SERVICES})
        if self.path.startswith("/knowledge/"):
            key = self.path.split("/knowledge/", 1)[1]
            item = get(key)
            return send_json(self, 200 if item else 404, item or {"error": "not_found"})
        return send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path not in ("/ask", "/build"):
            return send_json(self, 404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return send_json(self, 400, {"error": "invalid_json"})

        query = str(data.get("query", "")).strip()
        if not query:
            return send_json(self, 400, {"error": "query_required"})

        matches = search(query)
        if self.path == "/build":
            return send_json(self, 200, {
                "network": "xparallel-testnet",
                "mode": "build",
                "status": "accepted",
                "query": query,
                "matched_resources": matches,
                "next": "development workflow execution is the next testnet milestone"
            })

        return send_json(self, 200, {
            "network": "xparallel-testnet",
            "mode": "understand" if matches else "ask",
            "query": query,
            "results": matches,
            "message": "XParallel knowledge retrieved." if matches else "No matching testnet knowledge found yet."
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"XParallel Testnet v0.2 listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
