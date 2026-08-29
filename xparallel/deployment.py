"""Safe deployment-experiment adapter for a software project."""
from __future__ import annotations

from pathlib import Path

from .docker_runner import DockerUnavailable, run_in_sandbox
from .simulator import simulate


def deployment_experiment(project_dir: str, command: list[str]) -> dict:
    """Run an approved build/test command in the parallel sandbox.

    No production deployment is performed by this function.
    """
    project = Path(project_dir).resolve()
    try:
        result = run_in_sandbox(command, project)
        result["mode"] = "docker"
        return result
    except DockerUnavailable:
        fallback = simulate({"goal": "Deploy this project"})
        fallback["mode"] = "deterministic-fallback"
        fallback["limitations"].append("Docker is unavailable; no project command was executed")
        return fallback
