import tempfile,unittest
from xparallel.evolution_lab import EvolutionLab

class EvolutionLabTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.approve=True;self.p={"authenticated":True,"workspace_id":"w1","subject":"owner"}
  self.lab=EvolutionLab(authenticate=lambda s:self.p if s=="ok" else {"authenticated":False},
   authorize=lambda p,a,t:p["workspace_id"]=="w1",
   verify_approval=lambda p,pid,ref:self.approve and ref.startswith("human:"),
   run_evaluation=lambda req,ctx:{"metrics":{"accuracy":0.95},"baseline_metrics":{"accuracy":0.9},
     "candidate_metrics":{"accuracy":0.95},"regressions":[],"runner_id":"test-runner"},
   db_path=self.tmp.name+"/evo.sqlite")
 def tearDown(self):self.lab.close();self.tmp.cleanup()
 def experiment(self):
  return self.lab.run_experiment("ok",baseline_version="v1",candidate_version="v2",
    dataset=[{"input":"a","expected":"b"}],config={"seed":1})
 def test_reproducible_dataset_digest_and_approval_staged_lifecycle(self):
  exp=self.experiment();proposal=self.lab.propose("ok",experiment_id=exp["experiment_id"],artifact_digest="a"*64)
  with self.assertRaises(PermissionError):self.lab.stage("ok",proposal_id=proposal["proposal_id"],approval_ref="bad")
  self.lab.stage("ok",proposal_id=proposal["proposal_id"],approval_ref="human:stage")
  promoted=self.lab.promote("ok",proposal_id=proposal["proposal_id"],approval_ref="human:promote")
  self.assertFalse(promoted["deployment_performed"])
  self.assertEqual([x["event"] for x in self.lab.history("ok",proposal_id=proposal["proposal_id"])],
    ["proposed","staged","promoted"])
 def test_regressions_block_proposals(self):
  self.lab._runner=lambda *a:{"metrics":{"score":0.1},"regressions":["accuracy"]}
  exp=self.experiment()
  with self.assertRaises(ValueError):self.lab.propose("ok",experiment_id=exp["experiment_id"],artifact_digest="b"*64)
 def test_rollback_is_record_only_and_requires_reason(self):
  exp=self.experiment();p=self.lab.propose("ok",experiment_id=exp["experiment_id"],artifact_digest="c"*64)
  self.lab.stage("ok",proposal_id=p["proposal_id"],approval_ref="human:stage")
  result=self.lab.rollback("ok",proposal_id=p["proposal_id"],reason="staging regression")
  self.assertFalse(result["live_rollback_performed"])
 def test_workspace_and_authentication_isolation(self):
  with self.assertRaises(PermissionError):self.lab.run_experiment("bad",baseline_version="v1",candidate_version="v2",dataset=[{}],config={})
  self.p={"authenticated":True,"workspace_id":"w2","subject":"other"}
  with self.assertRaises(PermissionError):self.lab.run_experiment("ok",baseline_version="v1",candidate_version="v2",dataset=[{}],config={})
 def test_validation_and_immutable_version_pair(self):
  with self.assertRaises(ValueError):self.lab.run_experiment("ok",baseline_version="v1",candidate_version="v1",dataset=[{}],config={})
  with self.assertRaises(ValueError):self.lab.run_experiment("ok",baseline_version="v1",candidate_version="v2",dataset=[],config={})
if __name__=="__main__":unittest.main()
