"""Static regression checks for the XParallel portal UI contract."""
from pathlib import Path
import unittest


HTML = Path(__file__).resolve().parents[1] / "index.html"


class XParallelPortalUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = HTML.read_text(encoding="utf-8")

    def test_all_portal_areas_are_present(self):
        for feature in (
            "Verse Explorer",
            "Resource Map",
            "Parallel Mixer",
            "Route Console",
            "Build &amp; Repair Hub",
            "Dual Space",
            "Security &amp; Memory",
        ):
            with self.subTest(feature=feature):
                self.assertIn(feature, self.source)

    def test_portal_uses_only_existing_public_endpoints(self):
        for endpoint in (
            "/public/health",
            "/public/xparallel/access",
            "/public/system",
            "/public/route",
            "/public/build",
        ):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, self.source)

    def test_private_credentials_are_not_embedded_in_portal(self):
        self.assertIn("Never put provider secrets in browser code.", self.source)
        self.assertIn("Browser code deliberately stores no API secret", self.source)
        self.assertNotIn("XP_TOKEN =", self.source)
        self.assertNotIn("XP_EXECUTION_APPROVAL_TOKEN =", self.source)

    def test_dual_space_is_labeled_as_temporary_and_non_production(self):
        self.assertIn("Temporary local experiment only.", self.source)
        self.assertIn("does not clone production data or create a server sandbox", self.source)

    def test_repair_ui_does_not_claim_execution(self):
        self.assertIn("execution_performed:false", self.source)
        self.assertIn("A plan response is not proof of a repair or build being executed.", self.source)


if __name__ == "__main__":
    unittest.main()
