import json, unittest
from io import BytesIO
from unittest.mock import patch
from xparallel.cognitive_runtime import ModelGateway, OllamaLocalAdapter, ToolContractRegistry, evaluate_cases

class CognitiveRuntimeTests(unittest.TestCase):
    def test_local_first_provider_and_no_implicit_paid_fallback(self):
        calls=[]
        gateway=ModelGateway({"ollama-local":lambda r:calls.append("local") or {"text":"local answer","model":"tiny"},
                              "paid":lambda r:calls.append("paid") or {"text":"paid answer"}})
        result=gateway.generate([{"role":"user","content":"hello"}])
        self.assertEqual(result["provider"],"ollama-local"); self.assertEqual(calls,["local"])
        with self.assertRaises(RuntimeError):
            ModelGateway({"paid":lambda r:{"text":"x"}}).generate([{"role":"user","content":"hi"}],provider_order=["missing"])
    def test_context_and_output_budgets(self):
        gateway=ModelGateway({"local":lambda r:{"text":"ok"}},max_context_tokens=256,max_output_tokens=64)
        with self.assertRaises(ValueError):
            gateway.generate([{"role":"user","content":"x"*2000}])
        with self.assertRaises(ValueError):
            gateway.generate([{"role":"user","content":"hi"}],max_output_tokens=65)
    def test_structured_output_validation(self):
        gateway=ModelGateway({"local":lambda r:{"text":json.dumps({"ok":True,"count":2})}})
        schema={"type":"object","required":["ok"],"properties":{"ok":{"type":"boolean"},"count":{"type":"integer","minimum":0}},"additionalProperties":False}
        result=gateway.generate([{"role":"user","content":"return json"}],output_schema=schema)
        self.assertTrue(result["structured"]["ok"])
        bad=ModelGateway({"local":lambda r:{"text":'{"ok":"yes"}'}})
        with self.assertRaises(RuntimeError):
            bad.generate([{"role":"user","content":"json"}],output_schema=schema)
    def test_tool_proposals_require_authorization_and_never_execute(self):
        registry=ToolContractRegistry(authorize=lambda principal,name,args:principal.get("role")=="operator")
        registry.register("lookup","Read a record",{"type":"object","required":["id"],"properties":{"id":{"type":"string"}},"additionalProperties":False})
        proposal=registry.prepare_call({"role":"operator"},"lookup",{"id":"42"})
        self.assertEqual(proposal["status"],"proposal_only"); self.assertFalse(proposal["execution_performed"])
        with self.assertRaises(PermissionError):
            registry.prepare_call({"role":"viewer"},"lookup",{"id":"42"})
    def test_evaluation_harness_reports_exact_metrics(self):
        result=evaluate_cases([{"id":"a","input":1,"expected":2},{"id":"b","input":2,"expected":4}],
                              lambda x:x*2)
        self.assertEqual((result["passed"],result["failed"],result["pass_rate"]),(2,0,1.0))
    def test_ollama_adapter_restricts_network_to_loopback(self):
        with self.assertRaises(ValueError): OllamaLocalAdapter("model","http://example.com:11434/api/chat")
        adapter=OllamaLocalAdapter("model")
        response={"message":{"content":"local response"},"prompt_eval_count":2,"eval_count":3}
        with patch("xparallel.cognitive_runtime.urlopen") as open_url:
            open_url.return_value.__enter__.return_value=BytesIO(json.dumps(response).encode())
            result=adapter({"messages":[{"role":"user","content":"hi"}],"max_output_tokens":10})
        self.assertEqual(result["text"],"local response"); self.assertEqual(result["usage"],5)
if __name__=="__main__": unittest.main()
