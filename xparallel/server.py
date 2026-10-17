"""XParallel production API with V1 controlled execution."""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

from xparallel.agent import plan
from xparallel.connectors import connector_result
from xparallel.experiment import run_experiment
from xparallel.roaming import plan_roaming
from xparallel.roaming_engine import roam
from xparallel.router import route
from xparallel.store import get, load
from xparallel.v1_runner import available

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN")
APPROVAL_TOKEN = os.getenv("XP_EXECUTION_APPROVAL_TOKEN")
NETWORK = os.getenv("XP_NETWORK", "xparallel-mainnet")
VERSION = os.getenv("XP_VERSION", "1.0.0-v1")

SERVICES = [
    {"id": "knowledge", "name": "Knowledge Registry", "status": NETWORK},
    {"id": "service-registry", "name": "Service Registry", "status": NETWORK},
    {"id": "intent-router", "name": "Intent Router", "status": VERSION},
    {"id": "roaming-engine", "name": "OneAI Internet-Wide Roaming Engine", "status": "dynamic-roaming", "domain_restriction": False, "multi_worker": True},
    {"id": "parallel-sandbox", "name": "Controlled Docker Sandbox", "status": "v1", "available": available()},
    {"id": "execution-agent", "name": "Execution Agent", "status": "v1", "mode": "approval-gated"},
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
        return bool(TOKEN) and self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def execution_approved(self):
        return bool(APPROVAL_TOKEN) and self.headers.get("X-XParallel-Approval") == APPROVAL_TOKEN

    def do_GET(self):
        if self.path in ("/health", "/public/health"):
            return send_json(self, 200, {"status": "ok", "network": NETWORK, "version": VERSION, "sandbox_available": available()})
        if self.path == "/public/system":
            return send_json(self, 200, {
                "network": NETWORK, "version": VERSION, "services": SERVICES,
                "provider_mixer": "unverified", "memory_persistence": "unverified",
                "identity_provider": "unverified",
                "roaming_services": "dynamic_provider_roaming",
                "roaming_engine": "provider_neutral",
                "roaming_worker_registry": "environment_configured",
                "roaming_domain_restriction": False,
            })
        if self.path == "/public/xparallel/access":
            return send_json(self, 200, {
                "network": NETWORK, "api_authentication_required": True,
                "execution_approval_required": True, "sandbox_available": available(),
                "execution_endpoint_exposed_to_public_ui": False,
            })
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
        public_paths = ("/public/ask", "/public/build", "/public/route", "/public/roam")
        is_public = self.path in public_paths
        if not is_public and not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        if self.path not in ("/ask", "/build", "/route", "/fetch", "/agent/plan", "/experiment", "/execute", *public_paths):
            return send_json(self, 404, {"error": "not_found"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            max_length = 20_000 if is_public else 2_000_000
            if length > max_length:
                return send_json(self, 413, {"error": "request_too_large"})
            data = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(data, dict):
                return send_json(self, 400, {"error": "json_object_required"})
        except (ValueError, json.JSONDecodeError):
            return send_json(self, 400, {"error": "invalid_json"})

        if is_public:
            query = str(data.get("query", "")).strip()
            if not query:
                return send_json(self, 400, {"error": "query_required"})
            if len(query) > 12_000:
                return send_json(self, 413, {"error": "query_too_large"})
            if self.path == "/public/roam":
                try:
                    result = roam(query)
                except ValueError as exc:
                    code = str(exc)
                    return send_json(self, 413 if code == "query_too_large" else 400, {"error": code})
                result["network"] = NETWORK
                status = 200 if result["status"] == "success" else 503
                return send_json(self, status, result)
            if self.path == "/public/ask":
                return send_json(self, 503, {
                    "error": "mixer_unavailable",
                    "message": "No live AI provider call is available through this API yet.",
                    "setup": [
                        "Configure provider credentials as server-side environment secrets.",
                        "Implement and test provider adapters for the selected model families.",
                        "Record provider, model ID, latency, token counts, response hash, errors, and skipped-provider reasons.",
                        "Return a synthesized answer only after the configured mixer completes successfully.",
                    ],
                    "providers": [],
                })
            if self.path == "/public/route":
                return send_json(self, 200, {"network": NETWORK, **route(query)})
            return send_json(self, 200, {"network": NETWORK, **plan(query)})

        if self.path == "/fetch":
            url = str(data.get("url", "")).strip()
            if not url:
                return send_json(self, 400, {"error": "url_required"})
            return send_json(self, 200, connector_result(url))

        query = str(data.get("query", "")).strip()
        if not query:
            return send_json(self, 400, {"error": "query_required"})

        if self.path in ("/execute", "/experiment"):
            execution = data.get("execution")
            if not isinstance(execution, dict) or not execution.get("files"):
                return send_json(self, 400, {"error": "execution.files_required"})
            # API authentication and separate human approval are both required.
            if not self.execution_approved():
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
            "network": NETWORK, "mode": decision["mode"], "query": query,
            "results": decision["resources"],
            "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching knowledge found yet."
        })

    def log_message(self, *_):
        pass


if __name__ == "__main__":
    print(f"XParallel {NETWORK} {VERSION} listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
