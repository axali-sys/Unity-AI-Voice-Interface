"""XParallel V1 API: intent -> controlled sandbox -> evidence -> verified solution."""
import json
import os
import time
from urllib.parse import urlparse, parse_qs
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
from xparallel.axaliai_gateway import gateway_manifest
from xparallel.omni_unitai import system_manifest
from xparallel.memory_vault import save_memory, search_memories, list_memories, forget_memory
from xparallel.memory_service import summarize_memories
# SQLite conversation history remains default; PostgreSQL is explicitly opt-in.
if os.getenv("XP_CONVERSATION_BACKEND", "sqlite").strip().lower() == "postgres":
    from xparallel.conversation_store_postgres import save_conversation, get_conversation, list_conversations, delete_conversation
else:
    from xparallel.conversation_store import save_conversation, get_conversation, list_conversations, delete_conversation
from xparallel.chat_service import chat as chat_with_ai
from xparallel.parallel_world import create_parallel_plan
from xparallel.repair_jobs import create_job, get_job, list_jobs
# SQLite remains the default. PostgreSQL is opt-in and fails closed if misconfigured.
if os.getenv("XP_VERSE_BACKEND", "sqlite").strip().lower() == "postgres":
    from xparallel.parallel_verse_postgres import (
        register_agent, list_agents, create_space, list_spaces,
        record_event, list_events, create_task, list_tasks, discover_agents,
    )
else:
    from xparallel.parallel_verse import (
        register_agent, list_agents, create_space, list_spaces,
        record_event, list_events, create_task, list_tasks, discover_agents,
    )

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
    origin = handler.headers.get("Origin", "")
    # Allow configured frontend origins to call private endpoints with a bearer token.
    # CORS is not authorization: every private route still checks XP_TOKEN.
    if origin in PUBLIC_ORIGINS:
        handler.send_header("Access-Control-Allow-Origin", origin)
        handler.send_header("Vary", "Origin")
        handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-XParallel-Approval")
    handler.end_headers()
    handler.wfile.write(body)

def public_allowed(handler):
    origin = handler.headers.get("Origin", "")
    if origin in PUBLIC_ORIGINS:
        return True
    if not origin:
        host = handler.headers.get("Host", "").split(":", 1)[0].lower()
        return host.endswith(".vercel.app") or host in {"axaliai.com", "www.axaliai.com"}
    return False

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

def retrieve_memory_context(query, data):
    """Return a small, workspace-scoped memory context for authenticated AI workflows."""
    workspace = workspace_context(data)["workspace_id"]
    matches = search_memories(query, workspace, limit=3)
    return [
        {
            "id": item.get("id"),
            "summary": item.get("summary", ""),
            "content": str(item.get("content", ""))[:4000],
            "tags": item.get("tags", []),
            "score": item.get("score", 0),
        }
        for item in matches
    ]


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
        origin = self.headers.get("Origin", "")
        if not public_allowed(self) or (origin and origin not in PUBLIC_ORIGINS):
            return send_json(self, 403, {"error": "origin_not_allowed"})
        self.send_response(204)
        if origin and origin in PUBLIC_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-XParallel-Approval")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            return send_json(self, 200, {"status": "ok", "network": NETWORK, "version": VERSION, "sandbox_available": available()})
        if self.path == "/public/xparallel/access":
            if not public_allowed(self):
                return send_json(self, 403, {"error": "origin_not_allowed"}, cors=True)
            return send_json(self, 200, gateway_manifest(), cors=True)
        if self.path == "/public/system":
            if not public_allowed(self):
                return send_json(self, 403, {"error": "origin_not_allowed"}, cors=True)
            return send_json(self, 200, system_manifest(), cors=True)
        if self.path == "/public/health":
            if not public_allowed(self):
                return send_json(self, 403, {"error": "origin_not_allowed"}, cors=True)
            return send_json(self, 200, {"status": "ok", "network": NETWORK, "version": VERSION, "sandbox_available": available()}, cors=True)
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})
        parsed = urlparse(self.path)
        if parsed.path == "/verse/discovery":
            if not self.require_role("read"):
                return send_json(self, 403, {"error": "forbidden"})
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            try:
                limit = params.get("limit", ["50"])[0]
                capability = params.get("capability", [""])[0]
                agents = discover_agents(workspace, capability=capability, limit=limit)
                return send_json(self, 200, {
                    "workspace_id": workspace,
                    "capability_query": capability,
                    "match_basis": "declared agent kind/capabilities metadata",
                    "runtime_verified": False,
                    "count": len(agents),
                    "agents": agents,
                })
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
        if parsed.path in {"/verse/agents", "/verse/spaces", "/verse/events", "/verse/tasks"}:
            if not self.require_role("read"):
                return send_json(self, 403, {"error": "forbidden"})
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            try:
                limit = params.get("limit", ["50"])[0]
                if parsed.path == "/verse/agents":
                    items = list_agents(workspace, limit)
                    return send_json(self, 200, {"workspace_id": workspace, "agents": items})
                if parsed.path == "/verse/spaces":
                    items = list_spaces(workspace, limit)
                    return send_json(self, 200, {"workspace_id": workspace, "spaces": items})
                if parsed.path == "/verse/events":
                    items = list_events(workspace, limit)
                    return send_json(self, 200, {"workspace_id": workspace, "events": items})
                items = list_tasks(workspace, limit)
                return send_json(self, 200, {"workspace_id": workspace, "tasks": items})
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
        if parsed.path == "/repair/jobs":
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            try:
                jobs = list_jobs(workspace, params.get("limit", ["50"])[0], params.get("status", [""])[0])
            except ValueError:
                return send_json(self, 400, {"error": "invalid_limit"})
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace, "jobs": jobs})
        if parsed.path.startswith("/repair/jobs/"):
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            job_id = parsed.path.rsplit("/", 1)[-1]
            job = get_job(job_id, workspace)
            return send_json(self, 200 if job else 404, job or {"error": "not_found"})
        if parsed.path == "/conversations":
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            limit = params.get("limit", ["50"])[0]
            try:
                conversations = list_conversations(workspace, limit)
            except (ValueError, TypeError):
                return send_json(self, 400, {"error": "invalid_limit"})
            return send_json(self, 200, {"workspace_id": workspace, "conversations": conversations})
        if parsed.path.startswith("/conversations/"):
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            conversation_id = parsed.path.rsplit("/", 1)[-1]
            conversation = get_conversation(conversation_id, workspace)
            return send_json(self, 200 if conversation else 404, conversation or {"error": "not_found"})
        if parsed.path == "/memory":
            params = parse_qs(parsed.query)
            workspace = workspace_context({"workspace_id": params.get("workspace_id", ["default"])[0]})["workspace_id"]
            limit = params.get("limit", ["50"])[0]
            query = params.get("q", [""])[0]
            if query:
                return send_json(self, 200, {"memories": search_memories(query, workspace, limit)})
            return send_json(self, 200, {"memories": list_memories(workspace, limit)})
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

        if self.path in {"/verse/agents", "/verse/spaces", "/verse/events", "/verse/tasks"}:
            if not self.require_role("create_solution"):
                return send_json(self, 403, {"error": "forbidden"})
            workspace_data = workspace_context(data)
            workspace = workspace_data["workspace_id"]
            try:
                if self.path == "/verse/agents":
                    result = register_agent(workspace, data.get("name", ""), data.get("kind", "general"),
                                            data.get("metadata") if isinstance(data.get("metadata"), dict) else {})
                    self.audit("verse_agent_registered", workspace, workspace_data["actor"], {"agent_id": result["agent_id"]})
                    return send_json(self, 201, result)
                if self.path == "/verse/spaces":
                    result = create_space(workspace, data.get("name", ""), data.get("description", ""))
                    self.audit("verse_space_created", workspace, workspace_data["actor"], {"space_id": result["space_id"]})
                    return send_json(self, 201, result)
                if self.path == "/verse/events":
                    result = record_event(workspace, data.get("event_type", ""), data.get("payload", {}),
                                          data.get("space_id"), data.get("agent_id"))
                    self.audit("verse_event_recorded", workspace, workspace_data["actor"], {"event_id": result["event_id"]})
                    return send_json(self, 201, result)
                result = create_task(workspace, data.get("title", ""), data.get("description", ""),
                                     data.get("space_id"), data.get("created_by"), data.get("assigned_to"))
                self.audit("verse_task_created", workspace, workspace_data["actor"], {"task_id": result["task_id"]})
                return send_json(self, 201, result)
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})

        if self.path == "/conversations":
            workspace = workspace_context(data)["workspace_id"]
            try:
                result = save_conversation(data.get("conversation_id", ""), workspace, data.get("title", "New chat"), data.get("messages", []))
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
            self.audit("conversation_saved", workspace, workspace_context(data)["actor"], {"conversation_id": result["conversation_id"], "message_count": result["message_count"]})
            return send_json(self, 200, result)

        if self.path == "/conversations/delete":
            workspace = workspace_context(data)["workspace_id"]
            conversation_id = str(data.get("conversation_id", "")).strip()
            if not conversation_id:
                return send_json(self, 400, {"error": "conversation_id_required"})
            deleted = delete_conversation(conversation_id, workspace)
            self.audit("conversation_deleted", workspace, workspace_context(data)["actor"], {"conversation_id": conversation_id, "deleted": deleted})
            return send_json(self, 200 if deleted else 404, {"deleted": deleted})

        if self.path == "/repair/jobs":
            if not self.require_role("create_solution"):
                return send_json(self, 403, {"error": "forbidden"})
            query = str(data.get("query", "")).strip()
            job_type = str(data.get("job_type", "diagnostic")).strip()
            if not query:
                return send_json(self, 400, {"error": "query_required"})
            if len(query) > 4000:
                return send_json(self, 400, {"error": "query_too_large"})
            if job_type not in {"diagnostic", "repair_plan"}:
                return send_json(self, 400, {"error": "unsupported_job_type"})
            workspace_data = workspace_context(data)
            try:
                try:
                    context = retrieve_memory_context(query, data)
                    plan_result = plan(query, context)
                    result = {
                        "diagnosis": {
                            "status": "preliminary",
                            "message": "Generated a plan from the current router and authorized workspace memory. This is not a verified root-cause finding.",
                            "observed_resources": plan_result.get("resources", []),
                        },
                        "plan": plan_result,
                        "verification": {"status": "not_run", "reason": "No target repository, service probe, or test suite was executed by this plan-only endpoint."},
                    }
                    job_status, job_error = "completed", None
                except Exception:
                    result = {
                        "diagnosis": {
                            "status": "failed",
                            "message": "Planning could not complete. Internal exception details are not exposed by this endpoint.",
                            "observed_resources": [],
                        },
                        "plan": None,
                        "verification": {"status": "not_run", "reason": "Planning failed before verification could start."},
                    }
                    job_status, job_error = "failed", "planning_failed"
                job = create_job(
                    workspace_id=workspace_data["workspace_id"],
                    actor=workspace_data["actor"],
                    query=query,
                    result=result,
                    job_type=job_type,
                    status=job_status,
                    error=job_error,
                )
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
            self.audit("repair_job_planned", workspace_data["workspace_id"], workspace_data["actor"], {
                "job_id": job["job_id"], "job_type": job_type, "execution_performed": False,
            })
            return send_json(self, 201, {"network": NETWORK, "job": job})

        if self.path == "/fetch":
            url = str(data.get("url", "")).strip()
            if not url:
                return send_json(self, 400, {"error": "url_required"})
            return send_json(self, 200, connector_result(url))

        if self.path == "/public/solutions":
            workspace = workspace_context(data)["workspace_id"]
            limit = max(1, min(int(data.get("limit", 50)), 100))
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace,
                "solutions": REPOSITORY.list(workspace, limit=limit)}, cors=True)

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

        if self.path == "/memory/save":
            try:
                result = save_memory(
                    content=data.get("content", ""),
                    workspace_id=workspace_context(data)["workspace_id"],
                    summary=str(data.get("summary", "")),
                    tags=data.get("tags") if isinstance(data.get("tags"), list) else [],
                )
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
            workspace = workspace_context(data)["workspace_id"]
            self.audit("memory_saved", workspace, workspace_context(data)["actor"], {
                "memory_id": result["id"], "created": result["created"],
            })
            return send_json(self, 201 if result["created"] else 200, result)

        if self.path == "/memory/search":
            memory_query = str(data.get("query", "")).strip()
            if not memory_query:
                return send_json(self, 400, {"error": "query_required"})
            workspace = workspace_context(data)["workspace_id"]
            limit = max(1, min(int(data.get("limit", 10)), 50))
            memories = search_memories(memory_query, workspace, limit)
            self.audit("memory_searched", workspace, workspace_context(data)["actor"], {
                "result_count": len(memories), "query_length": len(memory_query),
            })
            return send_json(self, 200, {"memories": memories})

        if self.path == "/chat":
            messages = data.get("messages")
            workspace = workspace_context(data)["workspace_id"]
            use_memory = data.get("use_memory", True) is not False
            try:
                result = chat_with_ai(messages, workspace, use_memory)
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
            except RuntimeError as exc:
                error = str(exc)
                status = 503 if error in {"ai_provider_not_configured", "ai_provider_url_must_use_https"} else 502
                return send_json(self, status, {"error": error})
            self.audit("axaliai_chat", workspace, workspace_context(data)["actor"], {
                "model": result.get("model", "unknown"),
                "message_count": len(messages) if isinstance(messages, list) else 0,
            })
            return send_json(self, 200, {"network": NETWORK, "workspace_id": workspace, **result})

        if self.path == "/memory/summarize":
            memory_query = str(data.get("query", "")).strip()
            if not memory_query:
                return send_json(self, 400, {"error": "query_required"})
            workspace = workspace_context(data)["workspace_id"]
            limit = max(1, min(int(data.get("limit", 5)), 10))
            try:
                result = summarize_memories(memory_query, workspace, limit)
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
            except RuntimeError as exc:
                error = str(exc)
                status = 503 if error in {"ai_provider_not_configured", "ai_provider_url_must_use_https"} else 502
                return send_json(self, status, {"error": error})
            self.audit("memory_summarized", workspace, workspace_context(data)["actor"], {
                "provider": result.get("provider", "unknown"),
                "source_count": len(result.get("memories", [])),
                "query_length": len(memory_query),
            })
            return send_json(self, 200, result)

        if self.path == "/world/plan":
            query = str(data.get("query", "")).strip()
            if not query:
                return send_json(self, 400, {"error": "query_required"})
            if len(query) > 4000:
                return send_json(self, 400, {"error": "query_too_large"})
            workspace = workspace_context(data)["workspace_id"]
            try:
                result = create_parallel_plan(query, workspace)
            except ValueError as exc:
                return send_json(self, 400, {"error": str(exc)})
            except RuntimeError as exc:
                error = str(exc)
                status = 503 if error in {"ai_provider_not_configured", "ai_provider_url_must_use_https"} else 502
                return send_json(self, status, {"error": error})
            plan_data = result.get("plan", {})
            self.audit("parallel_world_plan_created", workspace, workspace_context(data)["actor"], {
                "provider": plan_data.get("provider", "unknown"),
                "memory_source_count": len(plan_data.get("memory_sources", [])),
            })
            return send_json(self, 200, result)

        if self.path == "/memory/forget":
            memory_id = str(data.get("id", "")).strip()
            if not memory_id:
                return send_json(self, 400, {"error": "id_required"})
            workspace = workspace_context(data)["workspace_id"]
            deleted = forget_memory(memory_id, workspace)
            self.audit("memory_forgotten", workspace, workspace_context(data)["actor"], {
                "memory_id": memory_id, "deleted": deleted,
            })
            return send_json(self, 200 if deleted else 404, {"deleted": deleted})

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
            context = retrieve_memory_context(query, data)
            return send_json(self, 200, {"network": NETWORK, **plan(query, context)})
        decision = route(query)
        if self.path == "/route":
            return send_json(self, 200, {"network": NETWORK, **decision})
        if self.path == "/build":
            context = retrieve_memory_context(query, data)
            return send_json(self, 200, {"network": NETWORK, **plan(query, context)})
        context = retrieve_memory_context(query, data)
        return send_json(self, 200, {"network": NETWORK, "mode": decision["mode"], "query": query,
            "results": decision["resources"], "memory_context": context,
            "message": "XParallel knowledge and memory retrieved." if decision["resources"] or context else "No matching knowledge or memory found yet."})

    def log_message(self, *_):
        pass

if __name__ == "__main__":
    print(f"XParallel {NETWORK} {VERSION} listening on {HOST}:{PORT}")
    HTTPServer((HOST, PORT), Handler).serve_forever()
