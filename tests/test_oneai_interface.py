from pathlib import Path
import unittest
from test_health_contract import XParallelHTTPContractTests


ROOT = Path(__file__).resolve().parents[1]


class OneAIInterfaceSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")

    def test_execute_mode_generates_a_plan_without_claiming_execution(self):
        self.assertIn("currentMode==='execute'?'Preparing an execution plan only; no action will be executed.'", self.html)
        self.assertIn("(currentMode==='plan'||currentMode==='build'||currentMode==='execute')?'/public/build':'/public/ask'", self.html)

    def test_provider_status_is_not_presented_as_verified(self):
        self.assertIn(".provider-mini .statusdot{margin-left:auto;width:7px;height:7px;background:var(--amber)", self.html)
        self.assertIn("Provider connectivity has not been verified", self.html)
        for label in (
            "Adapter present · connectivity unverified",
            "Claude adapter · unverified",
            "Gemini adapter · unverified",
            "Kimi adapter · unverified",
        ):
            with self.subTest(provider=label):
                self.assertIn(label, self.html)

    def test_xparallel_has_a_dedicated_workspace_and_live_read_only_diagnostics(self):
        self.assertIn('id="xparallelWorkspace"', self.html)
        self.assertIn('XPARALLEL — DNA OF AI', self.html)
        self.assertIn("loadXParallelDiagnostics", self.html)
        for endpoint in ("/public/health", "/public/xparallel/access", "/public/system"):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, self.html)
        self.assertIn("Planning is separate from execution", self.html)
        self.assertIn("It does not dispatch jobs", self.html)

    def test_workspace_keeps_existing_public_endpoint_contracts(self):
        self.assertIn("'/public/health'", self.html)
        self.assertIn("'/public/build'", self.html)
        self.assertIn("'/public/ask'", self.html)


if __name__ == "__main__":
    unittest.main()
