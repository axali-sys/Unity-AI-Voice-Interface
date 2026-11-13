"""Provider-neutral cognitive runtime and model gateway primitives."""
from __future__ import annotations
import json, math
from typing import Any, Callable
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def _schema_check(value:Any,schema:dict[str,Any],path:str="$")->None:
    if not isinstance(schema,dict): raise ValueError("invalid_output_schema")
    kind=schema.get("type")
    valid={"object":dict,"array":list,"string":str,"integer":int,"number":(int,float),"boolean":bool,"null":type(None)}
    if kind in valid:
        expected=valid[kind]
        if not isinstance(value,expected) or (kind in {"integer","number"} and isinstance(value,bool)):
            raise ValueError(f"structured_output_type_mismatch:{path}")
    if kind=="object":
        props=schema.get("properties",{})
        if not isinstance(props,dict): raise ValueError("invalid_output_schema_properties")
        required=schema.get("required",[])
        if not isinstance(required,list) or any(not isinstance(x,str) for x in required): raise ValueError("invalid_output_schema_required")
        missing=[x for x in required if x not in value]
        if missing: raise ValueError(f"structured_output_missing_required:{path}")
        if schema.get("additionalProperties") is False and any(k not in props for k in value):
            raise ValueError(f"structured_output_extra_property:{path}")
        for key,child in value.items():
            if key in props: _schema_check(child,props[key],f"{path}.{key}")
    if kind=="array":
        if "maxItems" in schema and len(value)>schema["maxItems"]: raise ValueError(f"structured_output_array_too_large:{path}")
        if "items" in schema:
            for i,item in enumerate(value): _schema_check(item,schema["items"],f"{path}[{i}]")
    if kind=="string":
        if "maxLength" in schema and len(value)>schema["maxLength"]: raise ValueError(f"structured_output_string_too_long:{path}")
        if "enum" in schema and value not in schema["enum"]: raise ValueError(f"structured_output_enum_mismatch:{path}")
    if kind in {"integer","number"}:
        if isinstance(value,float) and not math.isfinite(value): raise ValueError(f"structured_output_nonfinite:{path}")
        if "minimum" in schema and value<schema["minimum"]: raise ValueError(f"structured_output_below_minimum:{path}")
        if "maximum" in schema and value>schema["maximum"]: raise ValueError(f"structured_output_above_maximum:{path}")

class OllamaLocalAdapter:
    """Optional zero-cost Ollama-compatible adapter restricted to loopback hosts."""
    def __init__(self,model:str,endpoint:str="http://127.0.0.1:11434/api/chat"):
        parsed=urlparse(endpoint)
        if parsed.scheme!="http" or parsed.hostname not in {"localhost","127.0.0.1","::1"} or parsed.username or parsed.password:
            raise ValueError("ollama_endpoint_must_be_loopback_http")
        if not isinstance(model,str) or not model.strip() or len(model)>120: raise ValueError("invalid_ollama_model")
        self.model,self.endpoint=model.strip(),endpoint

    def __call__(self,request:dict[str,Any])->dict[str,Any]:
        body=json.dumps({"model":self.model,"messages":request["messages"],"stream":False,
            "options":{"num_predict":request["max_output_tokens"]}}).encode()
        req=Request(self.endpoint,data=body,method="POST",headers={"Content-Type":"application/json","Accept":"application/json"})
        try:
            with urlopen(req,timeout=60) as response: payload=json.loads(response.read(2_000_000).decode())
        except (HTTPError,URLError,TimeoutError,OSError,ValueError) as exc:
            raise RuntimeError("local_model_request_failed") from exc
        try: text=payload["message"]["content"]
        except (KeyError,TypeError) as exc: raise RuntimeError("local_model_invalid_response") from exc
        if not isinstance(text,str) or not text.strip(): raise RuntimeError("local_model_empty_response")
        return {"text":text.strip(),"provider":"ollama-local","model":self.model,
                "usage":payload.get("prompt_eval_count",0)+payload.get("eval_count",0)}

class ModelGateway:
    """Select only explicitly enabled adapters; local-first and no paid fallback by default."""
    def __init__(self,adapters:dict[str,Callable[[dict[str,Any]],dict[str,Any]]],
        max_context_tokens:int=8192,max_output_tokens:int=2048):
        if not isinstance(adapters,dict) or not adapters or any(not isinstance(k,str) or not callable(v) for k,v in adapters.items()):
            raise TypeError("model_adapters_required")
        if not 256<=max_context_tokens<=131072 or not 1<=max_output_tokens<=16384:
            raise ValueError("model_context_budget_out_of_range")
        self._adapters=dict(adapters); self.max_context_tokens=max_context_tokens; self.max_output_tokens=max_output_tokens

    def generate(self,messages:list[dict[str,str]],*,provider_order:list[str]|None=None,
        output_schema:dict[str,Any]|None=None,max_output_tokens:int|None=None)->dict[str,Any]:
        if not isinstance(messages,list) or not messages or len(messages)>50: raise ValueError("invalid_messages")
        normalized=[]
        for item in messages:
            if not isinstance(item,dict) or item.get("role") not in {"system","user","assistant"} or not isinstance(item.get("content"),str):
                raise ValueError("invalid_message")
            content=item["content"].strip()
            if not content or len(content)>20000: raise ValueError("invalid_message_content")
            normalized.append({"role":item["role"],"content":content})
        estimated=sum(len(m["content"]) for m in normalized)//4
        if estimated>self.max_context_tokens: raise ValueError("context_budget_exceeded")
        output_limit=max_output_tokens if max_output_tokens is not None else self.max_output_tokens
        if not isinstance(output_limit,int) or isinstance(output_limit,bool) or not 1<=output_limit<=self.max_output_tokens:
            raise ValueError("output_budget_exceeded")
        providers=provider_order or (["ollama-local"] if "ollama-local" in self._adapters else list(self._adapters)[:1])
        if not isinstance(providers,list) or not providers: raise ValueError("provider_order_required")
        errors=[]
        for provider in providers:
            adapter=self._adapters.get(provider)
            if adapter is None: errors.append("provider_not_enabled"); continue
            try:
                result=adapter({"messages":normalized,"max_output_tokens":output_limit,
                                "max_context_tokens":self.max_context_tokens})
                if not isinstance(result,dict) or not isinstance(result.get("text"),str) or not result["text"].strip():
                    raise RuntimeError("provider_invalid_response")
                text=result["text"].strip()
                response={"text":text,"provider":provider,"model":str(result.get("model","unknown")),
                          "usage":result.get("usage"),"context_estimate_tokens":estimated}
                if output_schema is not None:
                    try: structured=json.loads(text)
                    except json.JSONDecodeError as exc: raise ValueError("structured_output_invalid_json") from exc
                    _schema_check(structured,output_schema)
                    response["structured"]=structured
                return response
            except Exception as exc:
                errors.append(type(exc).__name__)
        raise RuntimeError("all_enabled_model_adapters_failed:"+",".join(errors[:5]))

class ToolContractRegistry:
    """Validate and authorize tool proposals; this module never executes tools."""
    def __init__(self,authorize:Callable[[dict[str,str],str,dict[str,Any]],bool]):
        if not callable(authorize): raise TypeError("trusted_tool_authorizer_required")
        self._authorize=authorize; self._contracts={}

    def register(self,name:str,description:str,input_schema:dict[str,Any])->None:
        if not isinstance(name,str) or not name.replace("_","").replace("-","").isalnum() or len(name)>80:
            raise ValueError("invalid_tool_name")
        if not isinstance(description,str) or not description.strip() or len(description)>500:
            raise ValueError("invalid_tool_description")
        if not isinstance(input_schema,dict) or input_schema.get("type")!="object":
            raise ValueError("tool_input_schema_must_be_object")
        if name in self._contracts: raise ValueError("tool_already_registered")
        self._contracts[name]={"description":description,"input_schema":input_schema}

    def prepare_call(self,principal:dict[str,str],name:str,arguments:dict[str,Any])->dict[str,Any]:
        contract=self._contracts.get(name)
        if contract is None: raise LookupError("tool_not_registered")
        _schema_check(arguments,contract["input_schema"])
        if self._authorize(principal,name,arguments) is not True: raise PermissionError("tool_call_not_authorized")
        return {"status":"proposal_only","tool":name,"arguments":arguments,
                "description":contract["description"],"execution_performed":False}

def evaluate_cases(cases:list[dict[str,Any]],runner:Callable[[Any],Any])->dict[str,Any]:
    """Run deterministic evaluation cases and report exact pass/fail counts."""
    if not isinstance(cases,list) or not cases or len(cases)>500: raise ValueError("invalid_evaluation_cases")
    if not callable(runner): raise TypeError("evaluation_runner_required")
    results=[]
    for case in cases:
        if not isinstance(case,dict) or "input" not in case or "expected" not in case:
            raise ValueError("invalid_evaluation_case")
        try:
            actual=runner(case["input"]); passed=actual==case["expected"]
            results.append({"id":str(case.get("id","case"))[:100],"passed":passed})
        except Exception as exc:
            results.append({"id":str(case.get("id","case"))[:100],"passed":False,"error":type(exc).__name__})
    passed=sum(1 for item in results if item["passed"])
    return {"passed":passed,"failed":len(results)-passed,"total":len(results),
            "pass_rate":passed/len(results),"results":results}
