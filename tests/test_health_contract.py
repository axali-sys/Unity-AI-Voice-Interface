import os
import subprocess
import sys
import threading
import time
import urllib.request
import json


def test_health_endpoint_contract():
    env = os.environ.copy()
    env.update({"XP_TOKEN": "test-token", "PORT": "18787", "XP_NETWORK": "test-network"})
    proc = subprocess.Popen([sys.executable, "xparallel/server.py"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        deadline = time.time() + 5
        while time.time() < deadline:
            try:
                with urllib.request.urlopen("http://127.0.0.1:18787/health", timeout=1) as response:
                    assert response.status == 200
                    payload = json.load(response)
                    assert payload["status"] == "ok"
                    assert payload["network"] == "test-network"
                    return
            except Exception:
                time.sleep(0.1)
        raise AssertionError("health endpoint did not become ready")
    finally:
        proc.terminate()
        proc.wait(timeout=3)
