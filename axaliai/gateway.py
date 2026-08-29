"""Axaliai gateway facade for XParallel V1."""
import json
import os
from urllib.request import Request, urlopen
XP_URL=os.getenv("XP_URL","http://127.0.0.1:8787").rstrip("/")
XP_TOKEN=os.getenv("XP_TOKEN","xparallel-test-token")
def xparallel(path,method="GET",payload=None,approval=None):
    body=None if payload is None else json.dumps(payload).encode(); headers={"Authorization":f"Bearer {XP_TOKEN}","Content-Type":"application/json"}
    if approval: headers["X-XParallel-Approval"]=approval
    req=Request(XP_URL+path,data=body,method=method,headers=headers)
    with urlopen(req,timeout=30) as response: return json.loads(response.read())
def ask(query): return xparallel("/ask","POST",{"query":query})
def build(query): return xparallel("/build","POST",{"query":query})
def experiment(query,files=None,test_command=None):
    execution=None
    if files:
        execution={"files":files}
        if test_command: execution["test_command"]=test_command
    return xparallel("/experiment","POST",{"query":query,"execution":execution} if execution else {"query":query})
def health(): return xparallel("/health")
