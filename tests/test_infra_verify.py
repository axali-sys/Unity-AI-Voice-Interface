"""Unit tests for the safe XParallel infrastructure smoke-check helpers."""
import unittest
from pathlib import Path
from unittest.mock import patch

from xparallel.infra_verify import _request, _short


class InfraVerifyTests(unittest.TestCase):
    @patch("xparallel.infra_verify.urllib.request.urlopen")
    def test_request_parses_json_success(self, urlopen):
        class Response:
            status = 200

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self, _limit):
                return b'{"status":"ok","network":"test"}'

        urlopen.return_value = Response()
        status, body = _request("https://example.invalid", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "ok")

    @patch("xparallel.infra_verify.urllib.request.urlopen")
    def test_request_does_not_expose_transport_error_text(self, urlopen):
        import urllib.error

        urlopen.side_effect = urllib.error.URLError("secret-bearing diagnostic")
        status, body = _request("https://example.invalid", "/health")
        self.assertIsNone(status)
        self.assertEqual(body, {"error": "transport_error", "error_type": "URLError"})
        self.assertNotIn("secret-bearing", str(body))

    def test_short_only_reports_requested_scalar_fields(self):
        payload = {"status": "ok", "token": "do-not-print", "count": 3, "nested": {"key": "value"}}
        summary = _short(payload, "status", "count", "token", "nested")
        self.assertEqual(summary, "status=ok, count=3")
        self.assertNotIn("do-not-print", summary)

    def test_render_blueprint_declares_server_side_integrations(self):
        config = (Path(__file__).resolve().parents[1] / "render.yaml").read_text(encoding="utf-8")
        for key in (
            "XP_TOKEN", "XP_EXECUTION_APPROVAL_TOKEN", "XP_MIXER_MODELS_JSON",
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "MOONSHOT_API_KEY",
            "TAVILY_API_KEY", "ONEAI_ROAMING_WORKERS", "ONEAI_ROAMING_ALLOWED_HOSTS",
            "XP_MEMORY_DB", "XP_DB_PATH",
        ):
            self.assertIn(f"- key: {key}", config)
        self.assertIn("https://xparallel-ai-infrast-q4lg.bolt.host", config)
        self.assertIn("healthCheckPath: /health", config)


if __name__ == "__main__":
    unittest.main()
