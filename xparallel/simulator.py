"""Parallel-world simulation adapter for XParallel V0.1.

When Docker is available, V0.1 uses a real isolated container for a fixed probe.
Otherwise it falls back to the deterministic simulation used by the first slice.
The real-world execution boundary remains unchanged.
"""
from datetime import datetime, timezone

from .docker_runner import docker_available, run_in_container


def _deterministic_simulation(intent: dict) -> dict:
    goal = intent["goal"]
    success = bool(goal.strip())
    return {
        "environment": "xparallel-sandbox-v0.1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "success" if success else "failed",
        "evidence": [
            "intent accepted",
            "deterministic sandbox simulation completed",
        ] if success else ["empty intent"],
        "implementation": {"type": "simulation-only", "goal": goal},
        "limitations": [
            "Docker was unavailable, so no real container was started",
            "Simulation success is not production proof",
        ],
    }


def simulate(intent: dict) -> dict:
    """Run the real isolated world when Docker is available; otherwise fallback."""
    if docker_available():
        result = run_in_container(intent)
        if result.get("status") in {"success", "failed"}:
            result.setdefault("limitations", [
                "Container probe is not production proof",
                "Real-world execution is disabled in V0.1",
            ])
            return result
    return _deterministic_simulation(intent)
