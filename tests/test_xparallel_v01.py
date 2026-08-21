from xparallel.experiment import run_experiment
from xparallel.intent import parse_intent


def test_parse_intent():
    intent = parse_intent("Deploy Axaliai V1")
    assert intent.goal == "Deploy Axaliai V1"
    assert intent.environment == "sandbox"
    assert intent.approval_required is True


def test_experiment_stops_at_human_boundary():
    result = run_experiment("Deploy Axaliai V1")
    assert result["simulation"]["status"] == "success"
    assert result["transfer"]["status"] == "ready_for_review"
    assert result["transfer"]["requires_human_approval"] is True
    assert result["transfer"]["real_world_execution"] == "not_performed"
