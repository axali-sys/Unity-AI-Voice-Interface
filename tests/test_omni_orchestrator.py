import unittest
from xparallel.omni_orchestrator import OmniOrchestrator

class OmniOrchestratorTests(unittest.TestCase):
    def make_engine(self,execute=None,approval=None,authorize=None,receipt=None):
        calls=[]
        engine=OmniOrchestrator(
          authorize_step=authorize or (lambda s,step:{"allowed":True}),
          check_approval=approval or (lambda s,step:{"approved":True,"ticket_id":"ticket-1"}),
          execute_step=execute or (lambda s,step:{"status":"completed","result":"ok"}),
          record_receipt=receipt or (lambda s,step,result:"receipt-1"),
          retry_wait=lambda seconds:calls.append(seconds),max_attempts=2)
        return engine,calls
    def workflow(self):
        return {"workflow_id":"demo","steps":[
          {"step_id":"one","action":"read.data","resource_scope":"dataset:1","input":{}},
          {"step_id":"two","action":"write.result","resource_scope":"result:1","input":{},
           "depends_on":["one"],"consequential":True,"requires_approval":True}]}
    def test_plan_orders_dependencies_and_requires_approval(self):
        engine,_=self.make_engine()
        plan=engine.plan(self.workflow())
        self.assertEqual([x["step_id"] for x in plan["steps"]],["one","two"])
        bad={"steps":[{"step_id":"x","action":"delete","resource_scope":"db:*","consequential":True}]}
        with self.assertRaises(ValueError): engine.plan(bad)
    def test_execution_requires_authorization_approval_and_receipt(self):
        engine,_=self.make_engine()
        result=engine.execute("session",self.workflow())
        self.assertEqual(result["status"],"completed")
        self.assertTrue(result["human_approval_enforced"])
        self.assertTrue(result["execution_performed"])
    def test_denied_policy_or_missing_approval_stops_execution(self):
        engine,_=self.make_engine(authorize=lambda s,step:{"allowed":False})
        self.assertEqual(engine.execute("session",self.workflow())["step_statuses"]["one"],"blocked_policy")
        engine,_=self.make_engine(approval=lambda s,step:{"approved":False})
        result=engine.execute("session",self.workflow())
        self.assertEqual(result["step_statuses"]["two"],"pending_approval")
    def test_idempotent_retry_is_bounded_and_receipt_failure_blocks(self):
        count={"n":0}
        def run(session,step):
            count["n"]+=1
            return {"status":"completed"} if count["n"]>1 else {"status":"failed","retryable":True}
        engine,waits=self.make_engine(execute=run)
        result=engine.execute("session",{"steps":[{"step_id":"a","action":"read","resource_scope":"r","idempotent":True}]})
        self.assertEqual(result["step_statuses"]["a"],"completed")
        self.assertEqual(waits,[2])
        engine,_=self.make_engine(receipt=lambda *a:None)
        result=engine.execute("session",{"steps":[{"step_id":"a","action":"write","resource_scope":"r","consequential":True,"requires_approval":True}]})
        self.assertEqual(result["step_statuses"]["a"],"executed_unreceipted")
    def test_cycles_unknown_dependencies_and_no_dependent_execution(self):
        engine,_=self.make_engine()
        with self.assertRaises(ValueError):
            engine.plan({"steps":[{"step_id":"a","action":"x","resource_scope":"r","depends_on":["b"]},{"step_id":"b","action":"x","resource_scope":"r","depends_on":["a"]}]})
        engine,_=self.make_engine(execute=lambda s,step:{"status":"failed"})
        result=engine.execute("session",{"steps":[{"step_id":"a","action":"x","resource_scope":"r"},{"step_id":"b","action":"y","resource_scope":"r","depends_on":["a"]}]})
        self.assertEqual(result["step_statuses"]["b"],"not_started")
if __name__=="__main__": unittest.main()
