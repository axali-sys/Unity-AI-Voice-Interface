import tempfile,unittest
from xparallel.reality_interface import RealityInterface

class RealityInterfaceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p={"authenticated":True,"workspace_id":"w1","subject":"operator"}
  self.consent=True;self.calls=[]
  self.interface=RealityInterface(authenticate=lambda s:self.p if s=="ok" else {"authenticated":False},
   authorize=lambda p,a,t:p["workspace_id"]=="w1",
   verify_consent=lambda p,c,r:self.consent and r=="consent:valid",
   simulate=lambda typ,payload:self.calls.append((typ,payload)) or {"would_do":"simulate only"},
   db_path=self.tmp.name+"/reality.sqlite")
 def tearDown(self):self.interface.close();self.tmp.cleanup()
 def register(self):
  return self.interface.register("ok",connector_id="device-1",connector_type="smart-device",
    scopes=["sensor.read"],consent_ref="consent:valid")
 def test_explicit_consent_and_scope_bound_simulation(self):
  registered=self.register();self.assertEqual(registered["environment"],"simulation_only")
  result=self.interface.simulate_action("ok",connector_id="device-1",scope="sensor.read",payload={"sensor":"temp"})
  self.assertFalse(result["external_execution_performed"]);self.assertEqual(len(self.calls),1)
  with self.assertRaises(PermissionError):
   self.interface.simulate_action("ok",connector_id="device-1",scope="device.unlock",payload={})
 def test_missing_consent_denies_registration(self):
  self.consent=False
  with self.assertRaises(PermissionError):self.register()
 def test_emergency_revocation_blocks_future_simulations(self):
  self.register();self.interface.revoke("ok",connector_id="device-1",reason="operator stop")
  with self.assertRaises(PermissionError):
   self.interface.simulate_action("ok",connector_id="device-1",scope="sensor.read",payload={})
  self.assertEqual([x["event"] for x in self.interface.audit("ok",connector_id="device-1")],
    ["registered","revoked"])
 def test_workspace_and_authentication_isolation(self):
  self.register()
  with self.assertRaises(PermissionError):
   self.interface.simulate_action("bad",connector_id="device-1",scope="sensor.read",payload={})
  self.p={"authenticated":True,"workspace_id":"w2","subject":"other"}
  with self.assertRaises(PermissionError):
   self.interface.simulate_action("ok",connector_id="device-1",scope="sensor.read",payload={})
 def test_expiry_and_scope_validation(self):
  with self.assertRaises(ValueError):
   self.interface.register("ok",connector_id="x",connector_type="device",scopes=["*"],consent_ref="consent:valid",expires_in_seconds=0)
  self.register()
  self.interface._db.execute("UPDATE reality_connectors SET expires_at='2000-01-01T00:00:00+00:00'");self.interface._db.commit()
  with self.assertRaises(PermissionError):
   self.interface.simulate_action("ok",connector_id="device-1",scope="sensor.read",payload={})
if __name__=="__main__":unittest.main()
