"""XParallel V1 experiment orchestration and evidence records."""
import uuid
from datetime import datetime, timezone

from .intent import parse_intent
from .simulator import simulate
from .v1_runner import run_project


def run_experiment(query: str, execution: dict | None = None) -> dict:
    intent = parse_intent(query).to_dict()
    experiment_id = f"XP-{uuid.uuid4().hex[:8].upper()}"

    if execution and execution.get("files"):
        result = run_project(execution)
        mode = "controlled_project_execution"
    else:
        result = simulate(intent)
        mode = "simulation"

    successful = result.get("status") == "success"
    return {
        "experiment_id": experiment_id,
        "intent": intent,
        "mode": mode,
        "result": result,
        "transfer": {
            "status": "ready_for_review" if successful else "blocked",
            "requires_human_approval": True,
            "real_world_execution": "not_performed",
            "production_deployment": "disabled_in_v1",
        },
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
