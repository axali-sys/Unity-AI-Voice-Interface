import os,tempfile,unittest
from xparallel import omni_genome as omni
class OmniTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.old=os.environ.get('OMNI_DB'); os.environ['OMNI_DB']=os.path.join(self.tmp.name,'omni.db')
 def tearDown(self):
  if self.old is None: os.environ.pop('OMNI_DB',None)
  else: os.environ['OMNI_DB']=self.old
  self.tmp.cleanup()
 def test_sources_versions_and_workspace_isolation(self):
  r=omni.create_record('a','claim','subject','v1',origin='file',source={'source_type':'file','source_ref':'spec.md'})
  self.assertEqual(r['status'],'received'); self.assertEqual(r['verification_status'],'unverified')
  self.assertIsNone(omni.get_record(r['id'],'b'))
  omni.update_record(r['id'],'a',subject='subject',content='v2')
  self.assertEqual([x['content'] for x in omni.list_versions(r['id'],'a')],['v1','v2'])
 def test_model_claim_requires_evidence_to_verify(self):
  r=omni.create_record('a','claim','subject','model output',origin='model')
  with self.assertRaises(ValueError): omni.verify_record(r['id'],'a',method='review',actor_id='human',result='verified',evidence={})
  r=omni.verify_record(r['id'],'a',method='human_review',actor_id='human',result='verified',evidence={'decision':'accepted'})
  self.assertEqual(r['verification_status'],'verified')
if __name__=='__main__': unittest.main()
