"""Experiment orchestration and evidence records for XParallel V0.1."""
import uuid
from datetime import datetime, timezone

from .intent import parse_intent
from .simulator import simulate


def run_experiment(query: str) -> dict:
    intent = parse_intent(query)
    result = simulate(intent.to_dict())
    return {
        "experiment_id": f"XP-{uuid.uuid4().hex[:8].upper()}",
        "intent": intent.to_dict(),
        "simulation": result,
        "transfer": {
            "status": "ready_for_review" if result["status"] == "success" else "blocked",
            "requires_human_approval": True,
            "real_world_execution": "not_performed",
        },
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
