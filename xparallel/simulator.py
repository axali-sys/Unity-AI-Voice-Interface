"""Minimal isolated simulation adapter for XParallel V0.1.

V0.1 deliberately does not execute arbitrary user code. It models an experiment
and returns deterministic evidence so the orchestration boundary can be tested
before a real container runner is introduced.
"""
from datetime import datetime, timezone


def simulate(intent: dict) -> dict:
    goal = intent["goal"]
    success = bool(goal.strip())
    return {
        "environment": "xparallel-sandbox-v0.1",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "success" if success else "failed",
        "evidence": [
            "intent accepted",
            "sandbox simulation completed",
        ] if success else ["empty intent"],
        "implementation": {
            "type": "simulation-only",
            "goal": goal,
        },
        "limitations": [
            "No arbitrary code execution in V0.1",
            "Simulation success is not production proof",
        ],
    }
