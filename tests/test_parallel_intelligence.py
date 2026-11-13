import unittest
from xparallel.parallel_intelligence import ParallelIntelligence

class ParallelIntelligenceTests(unittest.TestCase):
    def make_engine(self,conflicts=None):
        specialists={"researcher":lambda r:{"content":"Evidence A","evidence_refs":["source:a"]},
          "critic":lambda r:{"content":"Evidence B","evidence_refs":["source:b"]}}
        return ParallelIntelligence(specialists=specialists,
          verify_contribution=lambda task,role,item:{"status":"verified","reviewer":"test-verifier"},
          synthesize=lambda task,items:{"content":"Combined analysis","conflicts":conflicts or []})
    def test_verified_attributed_contributions_are_synthesized(self):
        result=self.make_engine().collaborate("Compare evidence")
        self.assertEqual(result["status"],"synthesized")
        self.assertEqual(result["verified_specialists"],["researcher","critic"])
        self.assertTrue(all(x["content_sha256"] for x in result["contributions"]))
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["execution_performed"])
    def test_unverified_contribution_forces_review(self):
        engine=ParallelIntelligence(specialists={"one":lambda r:{"content":"claim"}},
          verify_contribution=lambda *a:{"status":"rejected"},
          synthesize=lambda t,c:{"content":"not expected"})
        result=engine.collaborate("task")
        self.assertEqual(result["status"],"insufficient_verified_evidence")
        self.assertIsNone(result["synthesis"])
    def test_conflicts_are_not_silently_resolved(self):
        result=self.make_engine(["researcher_vs_critic"]).collaborate("task")
        self.assertEqual(result["status"],"disagreement_requires_review")
        self.assertEqual(result["conflicts"],["researcher_vs_critic"])
    def test_budgets_and_roles_are_enforced(self):
        engine=self.make_engine()
        with self.assertRaises(ValueError): engine.collaborate("task",roles=["researcher","critic","researcher"])
        with self.assertRaises(ValueError): engine.collaborate("x"*10001)
        with self.assertRaises(ValueError): engine.collaborate("task",roles=["unknown"])
    def test_verifier_must_be_independent_and_failure_is_inconclusive(self):
        one=lambda r:{"content":"claim"}
        with self.assertRaises(ValueError):
            ParallelIntelligence(specialists={"one":one},verify_contribution=one,synthesize=lambda t,c:{"content":"x"})
        engine=ParallelIntelligence(specialists={"one":one},verify_contribution=lambda *a:(_ for _ in ()).throw(RuntimeError()),
          synthesize=lambda t,c:{"content":"x"})
        self.assertEqual(engine.collaborate("task")["status"],"insufficient_verified_evidence")
if __name__=="__main__": unittest.main()
