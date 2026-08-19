"""XParallel production API for Axaliai."""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os

from store import get, load
from router import route
from connectors import connector_result
from agent import plan

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN")
NETWORK = os.getenv("XP_NETWORK", "xparallel-mainnet")
VERSION = os.getenv("XP_VERSION", "1.0.0")

if not TOKEN:
    raise RuntimeError("XP_TOKEN must be configured by the deployment environment")

SERVICES = [
    {"id": "knowledge", "name": "Knowledge Registry", "status": NETWORK},
    {"id": "service-registry", "name": "Service Registry", "status": NETWORK},
    {"id": "agent-router", "name": "Agent Router", "status": NETWORK},
    {"id": "execution-agent", "name": "Execution Agent", "status": NETWORK, "mode": "plan-only"},
    {"id": "external-sources", "name": "External Source Connectors", "status": NETWORK},
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
            return send_json(self, 200, {"status": "ok", "network": NETWORK, "version": VERSION})
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path == "/registry":
            return send_json(self, 200, {"network": NETWORK, "version": VERSION, "knowledge": list(load()), "services": SERVICES})
        if self.path == "/services":
            return send_json(self, 200, {"network": NETWORK, "services": SERVICES})
        if self.path.startswith("/knowledge/"):
            key = self.path.split("/knowledge/", 1)[1]
            item = get(key)
            return send_json(self, 200 if item else 404, item or {"error": "not_found"})
        return send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path not in ("/ask", "/build", "/route", "/fetch", "/agent/plan"):
            return send_json(self, 404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return send_json(self, 400, {"error": "invalid_json"})

        if self.path == "/fetch":
            url = str(data.get("url", "")).strip()
            if not url:
                return send_json(self, 400, {"error": "url_required"})
            return send_json(self, 200, connector_result(url))

        query = str(data.get("query", "")).strip()
        if not query:
            return send_json(self, 400, {"error": "query_required"})
        if self.path == "/agent/plan":
            return send_json(self, 200, {"network": NETWORK, **plan(query)})

        decision = route(query)
        if self.path == "/route":
            return send_json(self, 200, {"network": NETWORK, **decision})
        if self.path == "/build":
            return send_json(self, 200, {"network": NETWORK, **plan(query)})
        return send_json(self, 200, {
            "network": NETWORK, "mode": decision["mode"], "query": query,
            "results": decision["resources"],
            "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching knowledge found yet."
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"XParallel {NETWORK} v{VERSION} listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
