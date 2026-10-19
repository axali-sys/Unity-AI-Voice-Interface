import http.client
import json
import select
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request


class XParallelHTTPContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            cls.port = sock.getsockname()[1]
        env = os.environ.copy()
        env.update({
            "XP_TOKEN": "test-token",
            "XP_EXECUTION_APPROVAL_TOKEN": "test-approval-token",
            "PORT": str(cls.port),
            "XP_NETWORK": "test-network",
            "XP_PUBLIC_ORIGINS": "https://preview.vercel.app",
        })
        cls.proc = subprocess.Popen(
            [sys.executable, "xparallel/server.py"],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                response = cls.request("GET", "/health")
                if response[0] == 200 and response[1].get("status") == "ok":
                    break
            except Exception:
                time.sleep(0.1)
        else:
            stderr = cls.proc.stderr.read().decode("utf-8", errors="replace") if cls.proc.poll() is not None else ""
            raise AssertionError(f"XParallel server did not become ready. {stderr}")

    @classmethod
    def tearDownClass(cls):
        cls.proc.terminate()
        try:
            cls.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            cls.proc.kill()
            cls.proc.wait(timeout=3)
        if cls.proc.stderr:
            cls.proc.stderr.close()

    @classmethod
    def request(cls, method, path, payload=None, token=None, host="preview.vercel.app", approval=None):
        headers = {"Host": host, "Accept": "application/json"}
        data = None
        if payload is not None:
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode("utf-8")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if approval:
            headers["X-XParallel-Approval"] = approval
        req = urllib.request.Request(cls.base_url + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))
        except http.client.RemoteDisconnected as exc:
            details = ""
            if cls.proc.stderr:
                ready, _, _ = select.select([cls.proc.stderr], [], [], 0.2)
                if ready:
                    details = cls.proc.stderr.read1(4000).decode("utf-8", errors="replace")
            raise AssertionError(f"XParallel closed the connection without an HTTP response for {method} {path}. Server diagnostics: {details}") from exc

    def test_health_and_public_manifests_are_readable(self):
        for path in ("/public/health", "/public/xparallel/access", "/public/system"):
            with self.subTest(path=path):
                status, payload = self.request("GET", path)
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload.get("network"), "test-network")

    def test_public_task_routes_return_json(self):
        for path in ("/public/ask", "/public/build", "/public/route"):
            with self.subTest(path=path):
                status, payload = self.request("POST", path, {"query": "Explain XParallel task routing"})
                self.assertEqual(status, 200, payload)
                self.assertEqual(payload.get("network"), "test-network")

    def test_private_registry_requires_authentication(self):
        status, payload = self.request("GET", "/registry", host="localhost")
        self.assertEqual(status, 401)
        self.assertEqual(payload.get("error"), "unauthorized")

    def test_execution_requires_explicit_approval_even_for_owner(self):
        body = {"query": "run a controlled test", "execution": {"files": [{"path": "note.txt", "content": "safe test"}]}}
        status, payload = self.request("POST", "/execute", body, token="test-token", host="localhost")
        self.assertEqual(status, 403)
        self.assertEqual(payload.get("error"), "human_approval_required")


if __name__ == "__main__":
    unittest.main()
