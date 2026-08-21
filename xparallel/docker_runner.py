"""Optional Docker-backed isolated world for XParallel V0.1.

The runner accepts only a structured intent and executes a fixed probe inside a
minimal container. It never interpolates the user's intent into a shell command.
If Docker is unavailable, callers should fall back to the deterministic simulator.
"""
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone

IMAGE = os.getenv("XP_DOCKER_IMAGE", "alpine:3.20")
TIMEOUT_SECONDS = int(os.getenv("XP_DOCKER_TIMEOUT", "20"))
MEMORY = os.getenv("XP_DOCKER_MEMORY", "256m")
CPUS = os.getenv("XP_DOCKER_CPUS", "0.5")
PIDS = os.getenv("XP_DOCKER_PIDS", "64")


def docker_available() -> bool:
    """Return True only when the Docker CLI and daemon are usable."""
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
            check=False,
        ).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def run_in_container(intent: dict) -> dict:
    """Run a fixed, non-user-controlled probe in an isolated container."""
    goal = str(intent.get("goal", "")).strip()
    started = datetime.now(timezone.utc).isoformat()
    if not goal:
        return {"status": "failed", "error": "empty intent"}

    # The command is fixed. User text is passed only as JSON metadata to the
    # Python process and is never interpreted as shell syntax.
    payload = json.dumps({"goal": goal})
    script = (
        "import json,platform; "
        "x=json.loads(__import__('os').environ['XP_INTENT']); "
        "print('XP_CONTAINER_OK'); "
        "print('platform='+platform.platform()); "
        "print('intent_received='+str(bool(x.get('goal'))))"
    )
    command = [
        "docker", "run", "--rm",
        "--network", "none",
        "--read-only",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--memory", MEMORY,
        "--cpus", CPUS,
        "--pids-limit", PIDS,
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=32m",
        "-e", "XP_INTENT=" + payload,
        IMAGE,
        "python3", "-c", script,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "environment": "docker",
            "started_at": started,
            "status": "failed",
            "error": "container timeout",
        }
    except OSError as exc:
        return {
            "environment": "docker",
            "started_at": started,
            "status": "failed",
            "error": str(exc),
        }

    output = completed.stdout.strip().splitlines()
    success = completed.returncode == 0 and "XP_CONTAINER_OK" in output
    return {
        "environment": "docker",
        "image": IMAGE,
        "started_at": started,
        "status": "success" if success else "failed",
        "exit_code": completed.returncode,
        "evidence": output[-10:],
        "stderr": completed.stderr[-2000:],
        "isolation": {
            "network": "none",
            "root_filesystem": "read-only",
            "capabilities": "dropped-all",
            "no_new_privileges": True,
            "memory": MEMORY,
            "cpus": CPUS,
            "pids_limit": PIDS,
        },
        "implementation": {"type": "container-probe", "goal": goal},
    }
