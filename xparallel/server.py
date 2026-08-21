"""XParallel V0.1 API: intent -> parallel experiment -> evidence."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from xparallel.agent import plan
from xparallel.connectors import connector_result
from xparallel.experiment import run_experiment
from xparallel.router import route
from xparallel.store import get, load

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN", "xparallel-test-token")

SERVICES = [
    {"id": "knowledge", "name": "Knowledge Registry", "status": "testnet"},
    {"id": "service-registry", "name": "Service Registry", "status": "testnet"},
    {"id": "intent-router", "name": "Intent Router", "status": "v0.1"},
    {"id": "parallel-simulator", "name": "Parallel World Simulator", "status": "v0.1", "mode": "simulation-only"},
    {"id": "execution-agent", "name": "Execution Agent", "status": "testnet", "mode": "plan-only"},
    {"id": "external-sources", "name": "External Source Connectors", "status": "testnet"},
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
            return send_json(self, 200, {"status": "ok", "network": "xparallel-testnet", "version": "0.1.0"})
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path == "/registry":
            return send_json(self, 200, {"knowledge": list(load()), "services": SERVICES})
        if self.path == "/services":
            return send_json(self, 200, {"services": SERVICES})
        if self.path.startswith("/knowledge/"):
            key = self.path.split("/knowledge/", 1)[1]
            item = get(key)
            return send_json(self, 200 if item else 404, item or {"error": "not_found"})
        return send_json(self, 404, {"error": "not_found"})

    def do_POST(self):
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path not in ("/ask", "/build", "/route", "/fetch", "/agent/plan", "/experiment"):
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

        if self.path == "/experiment":
            return send_json(self, 200, {"network": "xparallel-testnet", **run_experiment(query)})
        if self.path == "/agent/plan":
            return send_json(self, 200, {"network": "xparallel-testnet", **plan(query)})

        decision = route(query)
        if self.path == "/route":
            return send_json(self, 200, {"network": "xparallel-testnet", **decision})
        if self.path == "/build":
            return send_json(self, 200, {"network": "xparallel-testnet", **plan(query)})
        return send_json(self, 200, {
            "network": "xparallel-testnet", "mode": decision["mode"], "query": query,
            "results": decision["resources"],
            "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching testnet knowledge found yet."
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"XParallel V0.1 listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
