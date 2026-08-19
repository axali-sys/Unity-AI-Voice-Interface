"""Axaliai Stream Host - Unity Technologies streaming host wrapper.

Runs the XParallel/Axaliai backend and exposes a lightweight Server-Sent Events
endpoint at /stream. The host never embeds API keys; production credentials are
provided through environment variables.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import threading
import time
from urllib.parse import parse_qs, urlparse

from xparallel.router import route
from xparallel.agent import plan

HOST = os.getenv("STREAM_HOST", os.getenv("XP_HOST", "0.0.0.0"))
PORT = int(os.getenv("PORT", os.getenv("STREAM_PORT", "8787")))
TOKEN = os.getenv("XP_TOKEN")
NETWORK = os.getenv("XP_NETWORK", "xparallel-mainnet")
VERSION = os.getenv("XP_VERSION", "1.0.0")
BRAND = os.getenv("STREAM_BRAND", "Stream Axaliai at Unity Technologies")

if not TOKEN:
    raise RuntimeError("XP_TOKEN must be configured by the deployment environment")


def send_json(handler, status, payload):
    body = json.dumps(payload).encode()
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


class StreamHandler(BaseHTTPRequestHandler):
    def authorized(self):
        return self.headers.get("Authorization") == f"Bearer {TOKEN}"

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            return send_json(self, 200, {
                "status": "ok", "service": "axaliai-stream-host",
                "network": NETWORK, "version": VERSION, "brand": BRAND
            })
        if parsed.path != "/stream":
            return send_json(self, 404, {"error": "not_found"})
        if not self.authorized():
            return send_json(self, 401, {"error": "unauthorized"})

        query = parse_qs(parsed.query).get("query", [""])[0].strip()
        if not query:
            return send_json(self, 400, {"error": "query_required"})

        decision = route(query)
        result = plan(query)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        events = [
            {"type": "stream.started", "network": NETWORK, "version": VERSION, "brand": BRAND},
            {"type": "route.completed", "mode": decision.get("mode"), "resources": decision.get("resources", [])},
            {"type": "plan.completed", "data": result},
            {"type": "stream.completed"},
        ]
        for event in events:
            self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
            self.wfile.flush()
            time.sleep(0.05)

    def log_message(self, *_):
        pass


def main():
    print(f"{BRAND} | {NETWORK} v{VERSION} | {HOST}:{PORT}")
    HTTPServer((HOST, PORT), StreamHandler).serve_forever()


if __name__ == "__main__":
    main()
