"""XParallel V1 API: intent -> controlled sandbox -> evidence -> verified solution."""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from xparallel.agent import plan
from xparallel.connectors import connector_result
from xparallel.experiment import run_experiment
from xparallel.router import route
from xparallel.solution import create_solution, verify_solution
from xparallel.graph import GRAPH
from xparallel.persistence import REPOSITORY
from xparallel.workspace import workspace_context
from xparallel.billing import usage_event, invoice_preview
from xparallel.authz import authorize
from xparallel.audit_repository import AUDIT_REPOSITORY
from xparallel.store import get, load
from xparallel.v1_runner import available

HOST = os.getenv("XP_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("XP_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN")
APPROVAL_TOKEN = os.getenv("XP_EXECUTION_APPROVAL_TOKEN")
NETWORK = os.getenv("XP_NETWORK", "xparallel-mainnet")
VERSION = os.getenv("XP_VERSION", "1.0.0")
DEFAULT_ROLE = os.getenv("XP_DEFAULT_ROLE", "owner")
PUBLIC_ORIGINS = {origin.strip().rstrip("/") for origin in os.getenv(
    "XP_PUBLIC_ORIGINS", "https://axaliai.com,https://www.axaliai.com"
).split(",") if origin.strip()}
PUBLIC_RATE_LIMIT = int(os.getenv("XP_PUBLIC_RATE_LIMIT", "30"))
PUBLIC_RATE_WINDOW = int(os.getenv("XP_PUBLIC_RATE_WINDOW", "60"))
_PUBLIC_REQUESTS = {}

SERVICES = [
    {"id": "knowledge", "name": "Knowledge Registry", "status": NETWORK},
    {"id": "service-registry", "name": "Service Registry", "status": NETWORK},
    {"id": "intent-router", "name": "Intent Router", "status": "v1"},
    {"id": "solution-engine", "name": "XParallel Solution Engine", "status": "v1"},
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
    return handler.headers.get("Origin", "") in PUBLIC_ORIGINS

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
        return bool(TOKEN) and self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def role(self):
        return DEFAULT_ROLE if self.authorized() else "viewer"

    def require_role(self, action):
        return authorize(self.role(), action)

    def audit(self, action, workspace, actor="system", metadata=None):
        return AUDIT_REPOSITORY.record(action, workspace, actor, metadata)

    def execution_approved(self):
        return bool(APPROVAL_TOKEN) and self.headers.get("X-XParallel-Approval") == APPROVAL_TOKEN

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 2000000:
            raise ValueError("request_too_large")
        data = json.loads(self.rfile.read(length) or b"{}")
        if not isinstance(data, dict):
            raise ValueError("invalid_json_object")
        return data

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
        public_paths = {"/public/ask", "/public/build", "/public/route", "/public/solution", "/public/verify", "/public/graph/search"}
        if is_public:
            if not public_allowed(self):
                return send_json(self, 403, {"error": "origin_not_allowed"}, cors=True)
            if not public_rate_ok(self):
                return send_json(self, 429, {"error": "rate_limit_exceeded"}, cors=True)
            if self.path not in public_paths:
                return send_json(self, 404, {"error": "not_found"}, cors=True)
        elif not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})

        try:
            data = self.read_json()
        except (ValueError, json.JSONDecodeError) as exc:
            error = str(exc) or "invalid_json"
            return send_json(self, 413 if error == "request_too_large" else 400, {"error": error}, cors=is_public)

        if self.path == "/fetch":
            url = str(data.get("url", "")).strip()
            if not url:
                return send_json(self, 400, {"error": "url_required"})
            return send_json(self, 200, connector_result(url))

        if self.path in {"/public/solution", "/solution"}:
            query = str(data.get("query", "")).strip()
            try:
                solution = create_solution(query)
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)}, cors=is_public)
            workspace = workspace_context(data)["workspace_id"]
            node = GRAPH.add(solution, status="candidate", tags=data.get("tags") or [])
            REPOSITORY.put(workspace, node)
            audit = self.audit("solution_created", workspace, workspace_context(data)["actor"], {"node_id": node["node_id"]})
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace,
                "solution": solution, "node": node,
                "billing": usage_event("solution_created", workspace)}, cors=is_public)

        if self.path in {"/public/verify", "/verify"}:
            try:
                result = verify_solution(data.get("solution"))
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)}, cors=is_public)
            return send_json(self, 200, {"network": NETWORK, **result}, cors=is_public)

        if self.path in {"/public/graph/search", "/graph/search"}:
            query = str(data.get("query", "")).strip()
            if not query:
                return send_json(self, 400, {"error": "query_required"}, cors=is_public)
            limit = int(data.get("limit", 10))
            workspace = workspace_context(data)["workspace_id"]
            candidates = REPOSITORY.list(workspace, limit=200)
            terms = {term.lower() for term in query.split() if len(term) > 2}
            scored = []
            for node in candidates:
                haystack = json.dumps(node.get("solution", {}), sort_keys=True).lower()
                score = sum(term in haystack for term in terms)
                if score:
                    scored.append((score, node))
            scored.sort(key=lambda item: -item[0])
            results = [node for _, node in scored[:max(1, min(limit, 50))]]
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace,
                "results": results, "billing": usage_event("graph_search", workspace)}, cors=is_public)

        query = str(data.get("query", "")).strip()
        if not query:
            return send_json(self, 400, {"error": "query_required"}, cors=is_public)

        if self.path == "/public/ask":
            decision = route(query)
            return send_json(self, 200, {"network": NETWORK, "mode": decision["mode"], "query": query,
                "results": decision["resources"], "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching knowledge found yet."}, cors=True)
        if self.path == "/public/route":
            return send_json(self, 200, {"network": NETWORK, **route(query)}, cors=True)
        if self.path == "/public/build":
            return send_json(self, 200, {"network": NETWORK, **plan(query)}, cors=True)

        private = {"/ask", "/build", "/route", "/agent/plan", "/experiment", "/execute", "/graph", "/graph/promote", "/billing/preview"}
        if self.path not in private:
            return send_json(self, 404, {"error": "not_found"})

        if self.path in ("/execute", "/experiment"):
            execution = data.get("execution")
            if not isinstance(execution, dict) or not execution.get("files"):
                return send_json(self, 400, {"error": "execution.files_required"})
            if self.path == "/execute" and not self.execution_approved():
                return send_json(self, 403, {"error": "human_approval_required"})
            result = run_experiment(query, execution)
            result["network"] = NETWORK
            return send_json(self, 200, result)

        if self.path == "/graph":
            workspace = workspace_context(data)["workspace_id"]
            if not self.require_role("read"):
                return send_json(self, 403, {"error":"forbidden"})
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace,
                "nodes": REPOSITORY.list(workspace)})

        if self.path == "/graph/promote":
            if not self.require_role("verify"):
                return send_json(self, 403, {"error":"forbidden"})
            workspace = workspace_context(data)["workspace_id"]
            node_id = str(data.get("node_id", "")).strip()
            if not node_id:
                return send_json(self, 400, {"error": "node_id_required"})
            node = REPOSITORY.get(workspace, node_id)
            if not node:
                return send_json(self, 404, {"error": "not_found"})
            if GRAPH.get(node_id) is None:
                GRAPH.add(node["solution"], status=node["status"], tags=node["tags"])
            promoted = GRAPH.promote(node_id)
            REPOSITORY.put(workspace, promoted)
            audit = self.audit("verification", workspace, workspace_context(data)["actor"], {"node_id": node_id})
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace,
                "node": promoted, "billing": usage_event("verification", workspace), "audit": audit})

        if self.path == "/billing/preview":
            if not self.require_role("billing"):
                return send_json(self, 403, {"error":"forbidden"})
            workspace = workspace_context(data)["workspace_id"]
            events = data.get("events") if isinstance(data.get("events"), list) else []
            audit = self.audit("billing_preview", workspace, workspace_context(data)["actor"])
            return send_json(self, 200, {"network": NETWORK, **invoice_preview(workspace, events), "audit": audit})

        if self.path == "/agent/plan":
            return send_json(self, 200, {"network": NETWORK, **plan(query)})
        decision = route(query)
        if self.path == "/route":
            return send_json(self, 200, {"network": NETWORK, **decision})
        if self.path == "/build":
            return send_json(self, 200, {"network": NETWORK, **plan(query)})
        return send_json(self, 200, {"network": NETWORK, "mode": decision["mode"], "query": query,
            "results": decision["resources"], "message": "XParallel knowledge retrieved." if decision["resources"] else "No matching knowledge found yet."})

    def log_message(self, *_):
        pass

if __name__ == "__main__":
    print(f"XParallel {NETWORK} {VERSION} listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
