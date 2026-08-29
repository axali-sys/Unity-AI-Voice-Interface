"""Controlled XParallel V1 project runner."""
import base64, os, shutil, subprocess, tempfile
from datetime import datetime, timezone
from pathlib import Path
IMAGE=os.getenv("XP_RUNNER_IMAGE","python:3.12-alpine"); TIMEOUT=int(os.getenv("XP_RUNNER_TIMEOUT","60")); MAX_FILES=int(os.getenv("XP_RUNNER_MAX_FILES","200")); MAX_FILE_BYTES=int(os.getenv("XP_RUNNER_MAX_FILE_BYTES",str(256*1024))); MEMORY=os.getenv("XP_RUNNER_MEMORY","512m"); CPUS=os.getenv("XP_RUNNER_CPUS","1.0"); PIDS=os.getenv("XP_RUNNER_PIDS","128")
def available():
    if shutil.which("docker") is None: return False
    try: return subprocess.run(["docker","info"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5).returncode==0
    except (OSError,subprocess.SubprocessError): return False
def _write_workspace(root,files):
    if not isinstance(files,dict) or not files: raise ValueError("files must be a non-empty object")
    if len(files)>MAX_FILES: raise ValueError("too many files")
    for name,encoded in files.items():
        path=Path(name)
        if path.is_absolute() or ".." in path.parts: raise ValueError("unsafe file path")
        if not isinstance(encoded,str): raise ValueError("file content must be base64 text")
        raw=base64.b64decode(encoded,validate=True)
        if len(raw)>MAX_FILE_BYTES: raise ValueError("file exceeds size limit")
        target=root/path; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
def run_project(intent):
    started=datetime.now(timezone.utc).isoformat(); files=intent.get("files"); test_command=str(intent.get("test_command","python -m unittest discover -v")).strip()
    if not test_command or len(test_command)>1000: return {"status":"failed","error":"invalid test_command"}
    if not available(): return {"environment":"docker","status":"blocked","error":"docker_unavailable"}
    with tempfile.TemporaryDirectory(prefix="xparallel-") as tmp:
        root=Path(tmp)
        try: _write_workspace(root,files)
        except (ValueError,OSError,base64.binascii.Error) as exc: return {"environment":"docker","status":"failed","error":str(exc)}
        command=["docker","run","--rm","--network","none","--read-only","--cap-drop","ALL","--security-opt","no-new-privileges","--memory",MEMORY,"--cpus",CPUS,"--pids-limit",PIDS,"--tmpfs","/tmp:rw,noexec,nosuid,size=64m","-v",f"{root}:/workspace:rw","-w","/workspace",IMAGE,"sh","-lc",test_command]
        try: completed=subprocess.run(command,capture_output=True,text=True,timeout=TIMEOUT,check=False)
        except subprocess.TimeoutExpired: return {"environment":"docker","status":"failed","error":"test_timeout","timeout_seconds":TIMEOUT}
        except OSError as exc: return {"environment":"docker","status":"failed","error":str(exc)}
        return {"environment":"docker","image":IMAGE,"started_at":started,"status":"success" if completed.returncode==0 else "failed","exit_code":completed.returncode,"stdout":completed.stdout[-10000:],"stderr":completed.stderr[-10000:],"test_command":test_command,"isolation":{"network":"none","root_filesystem":"read-only","capabilities":"dropped-all","no_new_privileges":True,"memory":MEMORY,"cpus":CPUS,"pids_limit":PIDS}}
