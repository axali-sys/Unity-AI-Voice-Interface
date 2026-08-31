"""XParallel V1 API: intent -> controlled sandbox -> evidence."""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from xparallel.agent import plan
from xparallel.connectors import connector_result
from xparallel.experiment import run_experiment
from xparallel.router import route
from xparallel.store import get, load
from xparallel.v1_runner import available

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN")
APPROVAL_TOKEN = os.getenv("XP_EXECUTION_APPROVAL_TOKEN")
NETWORK = os.getenv("XP_NETWORK", "xparallel-mainnet")
VERSION = os.getenv("XP_VERSION", "1.0.0")
PUBLIC_ORIGINS = {
    origin.strip().rstrip("/")
    for origin in os.getenv(
        "XP_PUBLIC_ORIGINS",
        "https://axaliai.com,https://www.axaliai.com",
    ).split(",")
    if origin.strip()
}
PUBLIC_RATE_LIMIT = int(os.getenv("XP_PUBLIC_RATE_LIMIT", "30"))
PUBLIC_RATE_WINDOW = int(os.getenv("XP_PUBLIC_RATE_WINDOW", "60"))
_PUBLIC_REQUESTS = {}

if not TOKEN:
    raise RuntimeError("XP_TOKEN must be configured by the deployment environment")

SERVICES = [
    {"id": "knowledge", "name": "Knowledge Registry", "status": NETWORK},
    {"id": "service-registry", "name": "Service Registry", "status": NETWORK},
    {"id": "intent-router", "name": "Intent Router", "status": "v1"},
    {"id": "parallel-sandbox", "name": "Controlled Docker Sandbox", "status": "v1", "available": available()},
    {"id": "execution-agent", "name": "Execution Agent", "status": "v1", "mode": "approval-gated"},
    {"id": "external-sources", "name": "External Source Connectors", "status": NETWORK},
]


def send_json(handler, status, payload, cors=False):
    body = json.dumps(payload, indent=2).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    if cors:
        origin = handler.headers.get("Origin", "")
        if origin in PUBLIC_ORIGINS:
            handler.send_header("Access-Control-Allow-Origin", origin)
            handler.send_header("Vary", "Origin")
            handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.end_headers()
    handler.wfile.write(body)


def public_allowed(handler):
    origin = handler.headers.get("Origin", "")
    return origin in PUBLIC_ORIGINS


def public_rate_ok(handler):
    now = time.time()
    key = handler.client_address[0]
    timestamps = [t for t in _PUBLIC_REQUESTS.get(key, []) if now - t < PUBLIC_RATE_WINDOW]
    if len(timestamps) >= PUBLIC_RATE_LIMIT:
        _PUBLIC_REQUESTS[key] = timestamps
        return False
    timestamps.append(now)
    _PUBLIC_REQUESTS[key] = timestamps
    return True


class Handler(BaseHTTPRequestHandler):
    def authorized(self):
        return self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def execution_approved(self):
        return bool(APPROVAL_TOKEN) and self.headers.get("X-XParallel-Approval") == APPROVAL_TOKEN

    def do_OPTIONS(self):
        if not self.path.startswith("/public/") or not public_allowed(self):
            return send_json(self, 403, {"error": "origin_not_allowed"})
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin"))
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            return send_json(self, 200, {"status": "ok", "network": NETWORK, "version": VERSION, "sandbox_available": available()})
        if self.path == "/public/health":
            if not public_allowed(self):
                return send_json(self, 403, {"error": "origin_not_allowed"}, cors=True)
            return send_json(self, 200, {"status": "ok", "network": NETWORK, "version": VERSION, "sandbox_available": available()}, cors=True)
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
        is_public = self.path.startswith("/public/")
        if is_public:
            if not public_allowed(self):
                return send_json(self, 403, {"error": "origin_not_allowed"}, cors=True)
            if not public_rate_ok(self):
                return send_json(self, 429, {"error": "rate_limit_exceeded"}, cors=True)
            allowed_paths = {"/public/ask", "/public/build", "/public/route"}
            if self.path not in allowed_paths:
                return send_json(self, 404, {"error": "not_found"}, cors=True)
        elif not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 2000000:
                return send_json(self, 413, {"error": "request_too_large"}, cors=is_public)
            data = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return send_json(self, 400, {"error": "invalid_json"}, cors=is_public)

        query = str(data.get("query", "")).strip()
        if not query:
            return send_json(self, 400, {"error": "query_required"}, cors=is_public)

        if self.path == "/public/ask":
            decision = route(query)
            return send_json(self, 200, {
                "network": NETWORK,
                "mode": decision["mode"],
                "query": query,
                "results": decision["resources"],
                "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching knowledge found yet.",
            }, cors=True)
        if self.path == "/public/route":
            return send_json(self, 200, {"network": NETWORK, **route(query)}, cors=True)
        if self.path == "/public/build":
            return send_json(self, 200, {"network": NETWORK, **plan(query)}, cors=True)

        if self.path not in ("/ask", "/build", "/route", "/fetch", "/agent/plan", "/experiment", "/execute"):
            return send_json(self, 404, {"error": "not_found"})

        if self.path == "/fetch":
            url = str(data.get("url", "")).strip()
            if not url:
                return send_json(self, 400, {"error": "url_required"})
            return send_json(self, 200, connector_result(url))

        if self.path in ("/execute", "/experiment"):
            execution = data.get("execution")
            if not isinstance(execution, dict) or not execution.get("files"):
                return send_json(self, 400, {"error": "execution.files_required"})
            if self.path == "/execute" and not self.execution_approved():
                return send_json(self, 403, {"error": "human_approval_required"})
            result = run_experiment(query, execution)
            result["network"] = NETWORK
            return send_json(self, 200, result)

        if self.path == "/agent/plan":
            return send_json(self, 200, {"network": NETWORK, **plan(query)})
        decision = route(query)
        if self.path == "/route":
            return send_json(self, 200, {"network": NETWORK, **decision})
        if self.path == "/build":
            return send_json(self, 200, {"network": NETWORK, **plan(query)})
        return send_json(self, 200, {
            "network": NETWORK,
            "mode": decision["mode"],
            "query": query,
            "results": decision["resources"],
            "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching knowledge found yet.",
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"XParallel {NETWORK} {VERSION} listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
