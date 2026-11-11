"""Vercel Python entrypoint with a same-origin authenticated XParallel chat proxy."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from xparallel.server import Handler, send_json, PUBLIC_ORIGINS


class VercelHandler(Handler):
    def _chat_origin_allowed(self):
        origin = self.headers.get("Origin", "").rstrip("/")
        host = self.headers.get("Host", "").split(":", 1)[0].lower()
        if origin in PUBLIC_ORIGINS:
            return True
        # Permit only same-origin browser calls to this Vercel/custom app host.
        parsed = urlparse(origin)
        return bool(
            origin
            and parsed.scheme == "https"
            and parsed.netloc.lower() == host
            and (host.endswith(".vercel.app") or host in {"axaliai.com", "www.axaliai.com"})
        )

    def do_POST(self):
        if self.path != "/api/chat":
            return super().do_POST()

        if not self._chat_origin_allowed():
            return send_json(self, 403, {"ok": False, "error": "origin_not_allowed", "fallback": False})

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2000000:
                return send_json(self, 400, {"ok": False, "error": "invalid_request_size", "fallback": False})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                return send_json(self, 400, {"ok": False, "error": "invalid_json_object", "fallback": False})
        except (ValueError, json.JSONDecodeError):
            return send_json(self, 400, {"ok": False, "error": "invalid_json", "fallback": False})

        query = payload.get("query", "")
        query = query.strip() if isinstance(query, str) else ""
        messages = payload.get("messages") if isinstance(payload.get("messages"), list) else []
        if not messages and query:
            messages = [{"role": "user", "content": query}]
        if not messages or len(messages) > 20:
            return send_json(self, 400, {"ok": False, "error": "messages_required_or_limit_exceeded", "fallback": False})

        backend_url = (os.getenv("XP_API_URL") or "").strip().rstrip("/")
        token = (os.getenv("XP_TOKEN") or "").strip()
        if not backend_url or not token:
            return send_json(self, 503, {"ok": False, "error": "xparallel_backend_not_configured", "fallback": False})
        parsed_backend = urlparse(backend_url)
        if parsed_backend.scheme != "https" or not parsed_backend.netloc:
            return send_json(self, 503, {"ok": False, "error": "xparallel_backend_url_invalid", "fallback": False})

        body = json.dumps({
            "query": query,
            # This legacy Python proxy is not a trusted login adapter. Never let
            # browser JSON select a tenant or enable shared memory. Keep it aligned
            # with the Next.js preview route until a server-verified session exists.
            "workspace_id": "preview",
            "actor": "elle-preview",
            "messages": messages,
            "use_memory": False,
        }).encode()
        request = Request(
            backend_url + "/chat",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json", "Accept": "application/json", "Authorization": "Bearer " + token},
        )
        try:
            with urlopen(request, timeout=50) as response:
                data = json.loads(response.read())
                status = response.status
        except HTTPError as exc:
            try:
                upstream = json.loads(exc.read())
            except Exception:
                upstream = {}
            code = 503 if exc.code >= 500 else 502
            return send_json(self, code, {
                "ok": False,
                "error": "xparallel_authentication_failed" if exc.code in (401, 403) else upstream.get("error", "upstream_request_failed"),
                "upstream_status": exc.code,
                "fallback": False,
            })
        except (URLError, TimeoutError, json.JSONDecodeError):
            return send_json(self, 502, {"ok": False, "error": "xparallel_backend_unreachable", "fallback": False})

        answer = data.get("answer") or data.get("message") or data.get("response") if isinstance(data, dict) else None
        if status < 200 or status >= 300 or not isinstance(answer, str) or not answer.strip():
            return send_json(self, 502, {"ok": False, "error": "ai_provider_empty_or_invalid_response", "fallback": False})
        data.update({"ok": True, "message": answer.strip(), "fallback": False, "source": "xparallel_authenticated_chat"})
        return send_json(self, 200, data)


handler = VercelHandler

__all__ = ["handler"]
