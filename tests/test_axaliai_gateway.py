import unittest
from xparallel.axaliai_gateway import gateway_manifest

class AxaliaiGatewayTests(unittest.TestCase):
    def test_manifest(self):
        m = gateway_manifest()
        self.assertEqual(m["gateway"], "axaliai")
        self.assertEqual(m["network"], "xparallel-mainnet")
        self.assertIn("build", m["capabilities"])
        self.assertFalse(m["browser_secret_required"])
        self.assertEqual(m["execution"], "human_approval_required")
        self.assertEqual(m["payment_capture"], "disabled")

if __name__ == "__main__":
    unittest.main()
