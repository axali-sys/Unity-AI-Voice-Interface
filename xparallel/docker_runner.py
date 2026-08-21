"""Controlled Docker sandbox for XParallel software deployment experiments.

This runner is intentionally narrow: it executes a repository-provided command
inside an isolated container, captures stdout/stderr/exit status, and never
performs real-world deployment. It is a bridge from V0.1 simulation toward a
real isolated parallel environment.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Iterable


class DockerUnavailable(RuntimeError):
    pass


def docker_available() -> bool:
    return shutil.which("docker") is not None


def run_in_sandbox(
    command: Iterable[str],
    project_dir: str | Path,
    *,
    image: str = "python:3.12-slim",
    timeout: int = 120,
) -> dict:
    if not docker_available():
        raise DockerUnavailable("Docker CLI is not available")

    project = Path(project_dir).resolve()
    if not project.is_dir():
        raise ValueError("project_dir must be an existing directory")

    argv = [str(x) for x in command]
    if not argv:
        raise ValueError("command must not be empty")

    with tempfile.TemporaryDirectory(prefix="xparallel-sandbox-") as tmp:
        # The temporary writable workspace prevents mutations to the source tree.
        workspace = Path(tmp) / "workspace"
        shutil.copytree(project, workspace)
        docker_cmd = [
            "docker", "run", "--rm",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=128",
            "--cpus=1",
            "--memory=512m",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=64m",
            "-v", f"{workspace}:/workspace:rw",
            "-w", "/workspace",
            image,
            *argv,
        ]
        completed = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return {
            "status": "success" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "environment": "docker-isolated",
            "real_world_execution": "not_performed",
        }
