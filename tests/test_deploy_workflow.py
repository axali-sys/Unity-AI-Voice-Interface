from pathlib import Path
import unittest


class RenderDeployWorkflowTests(unittest.TestCase):
    def test_missing_render_hook_cannot_be_silently_skipped(self):
        workflow = Path(".github/workflows/mainnet-deploy.yml").read_text(encoding="utf-8")
        self.assertNotIn("if: ${{ env.RENDER_DEPLOY_HOOK != '' }}", workflow)
        self.assertIn('if [ -z "$RENDER_DEPLOY_HOOK" ]; then', workflow)
        self.assertIn("Missing required GitHub Actions secret RENDER_DEPLOY_HOOK", workflow)
        self.assertIn('curl --fail --silent --show-error -X POST "$RENDER_DEPLOY_HOOK"', workflow)


if __name__ == "__main__":
    unittest.main()
