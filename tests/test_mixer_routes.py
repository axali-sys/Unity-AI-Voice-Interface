import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from unittest.mock import patch
from xparallel import server

class MixerRouteTests(unittest.TestCase):
    def setUp(self):
        self.httpd=HTTPServer(("127.0.0.1",0),server.Handler)
        self.thread=threading.Thread(target=self.httpd.serve_forever,daemon=True)
        self.thread.start()
        self.base=f"http://127.0.0.1:{self.httpd.server_port}"

    def tearDown(self):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=2)

    def post(self,path,payload,headers=None):
        req=urllib.request.Request(self.base+path,data=json.dumps(payload).encode(),
            headers={"Content-Type":"application/json",**(headers or {})},method="POST")
        try:
            with urllib.request.urlopen(req,timeout=3) as response:
                return response.status,json.loads(response.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code,json.loads(exc.read().decode())

    def test_public_mixer_filters_private_plugins(self):
        captured={}
        async def fake_mix(query,**kwargs):
            captured.update(kwargs)
            return {"state":"ok","final_answer":"public answer","plugin_results":[]}
        with patch.object(server,"TOKEN",None), patch.object(server,"mix_answers",new=fake_mix):
            status,body=self.post("/public/mix",{"query":"hello","plugins":["github","web_search","ai_memory"]},
                                  {"Origin":"https://axaliai.com"})
        self.assertEqual(status,200)
        self.assertEqual(body["final_answer"],"public answer")
        self.assertEqual(captured["plugin_ids"],["web_search"])
        self.assertFalse(captured["allow_private"])
        self.assertEqual(captured["workspace_id"],"")

    def test_private_mixer_uses_authenticated_workspace_not_request_body(self):
        captured={}
        async def fake_mix(query,**kwargs):
            captured.update(kwargs)
            return {"state":"ok","final_answer":"private answer","plugin_results":[]}
        with patch.dict(os.environ,{"XP_DEFAULT_WORKSPACE_ID":"tenant-alpha","XP_WORKSPACE_TOKENS_JSON":"{}"}), patch.object(server,"TOKEN","global-secret"), patch.object(server,"mix_answers",new=fake_mix):
            status,body=self.post("/mix",{"query":"private question","workspace_id":"attacker-workspace","plugins":["ai_memory"]},
                                  {"Authorization":"Bearer global-secret"})
        self.assertEqual(status,200)
        self.assertEqual(captured["workspace_id"],"tenant-alpha")
        self.assertTrue(captured["allow_private"])
        self.assertEqual(captured["plugin_ids"],["ai_memory"])

    def test_sandbox_approval_route_consumes_one_time_ticket(self):
        payload={"files":{"hello.py":"cHJpbnQoJ29rJyk="}}
        headers={"Authorization":"Bearer global-secret","X-XParallel-Approval":"approval-secret"}
        with patch.dict(os.environ,{"XP_DEFAULT_WORKSPACE_ID":"tenant-alpha","XP_WORKSPACE_TOKENS_JSON":"{}"}), \
             patch.object(server,"TOKEN","global-secret"), patch.object(server,"APPROVAL_TOKEN","approval-secret"), \
             patch.object(server,"execute_plugin",return_value={"state":"ok","plugin_id":"xparallel_sandbox"}) as execute, \
             patch.object(server.AUDIT_REPOSITORY,"record",return_value={"event_fingerprint":"test"}):
            status,issued=self.post("/plugins/approve",{"plugin_id":"xparallel_sandbox","action":"run_tests","payload":payload},headers)
            self.assertEqual(status,200)
            request={"plugin_id":"xparallel_sandbox","action":"run_tests","payload":payload,"approval_ticket":issued["approval_ticket"]}
            status,result=self.post("/plugins/execute",request,{"Authorization":"Bearer global-secret"})
            self.assertEqual(status,200)
            self.assertTrue(execute.call_args.kwargs["human_approved"])
            replay_status,_=self.post("/plugins/execute",request,{"Authorization":"Bearer global-secret"})
        self.assertEqual(replay_status,403)

    def test_private_mixer_rejects_missing_bearer_token(self):
        with patch.object(server,"TOKEN","global-secret"):
            status,body=self.post("/mix",{"query":"private question"})
        self.assertEqual(status,401)
        self.assertEqual(body["error"],"unauthorized")

if __name__=="__main__":
    unittest.main()
