import unittest

from xparallel.experiment import run_experiment
from xparallel.intent import parse_intent


class XParallelV01Tests(unittest.TestCase):
    def test_parse_intent(self):
        intent = parse_intent("Deploy Axaliai V1")
        self.assertEqual(intent.goal, "Deploy Axaliai V1")
        self.assertEqual(intent.environment, "sandbox")
        self.assertTrue(intent.approval_required)

    def test_experiment_stops_at_human_boundary(self):
        result = run_experiment("Deploy Axaliai V1")
        self.assertEqual(result["result"]["status"], "success")
        self.assertEqual(result["transfer"]["status"], "ready_for_review")
        self.assertTrue(result["transfer"]["requires_human_approval"])
        self.assertEqual(result["transfer"]["real_world_execution"], "not_performed")


if __name__ == "__main__":
    unittest.main()
