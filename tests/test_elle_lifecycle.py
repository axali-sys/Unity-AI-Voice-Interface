import os,tempfile,unittest
from xparallel import elle_lifecycle as elle
class ElleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.old=os.environ.get('ELLE_DB'); os.environ['ELLE_DB']=os.path.join(self.tmp.name,'elle.db')
 def tearDown(self):
  if self.old is None: os.environ.pop('ELLE_DB',None)
  else: os.environ['ELLE_DB']=self.old
  self.tmp.cleanup()
 def test_high_risk_requires_human_approval(self):
  t=elle.create_task('a','owner','objective','outcome',risk_level='high')
  self.assertIsNone(elle.get_task(t['id'],'b'))
  for s in ('REMEMBER','PLAN','RESEARCH','BUILD','VERIFY','APPROVE'): t=elle.transition(t['id'],'a','owner',s)
  with self.assertRaises(PermissionError): elle.transition(t['id'],'a','owner','EXECUTE')
  with self.assertRaises(PermissionError): elle.approve_task(t['id'],'a','model:elle',authorized=True)
  elle.approve_task(t['id'],'a','human-reviewer',authorized=True)
  t=elle.transition(t['id'],'a','owner','EXECUTE'); self.assertEqual(t['state'],'EXECUTE')
 def test_invalid_transition_is_rejected(self):
  t=elle.create_task('a','owner','objective','outcome')
  with self.assertRaises(ValueError): elle.transition(t['id'],'a','owner','EXECUTE')
 def test_verification_requires_verify_state_and_evidence(self):
  t=elle.create_task('a','owner','objective','outcome')
  for s in ('REMEMBER','PLAN','RESEARCH','BUILD','VERIFY'): t=elle.transition(t['id'],'a','owner',s)
  t=elle.submit_verification(t['id'],'a','reviewer','passed',{'test':'unit','result':'pass'})
  self.assertEqual(t['verification']['result'],'passed')
if __name__=='__main__': unittest.main()
