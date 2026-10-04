from xparallel.solution import create_solution, verify_solution


def test_solution_is_deterministically_fingerprinted():
    record = create_solution("Build a secure customer portal")
    result = verify_solution(record)
    assert record["current_stage"] == "INTAKE"
    assert result["verified"] is True
    assert len(record["fingerprint"]) == 64


def test_tampering_invalidates_verification():
    record = create_solution("Build a secure customer portal")
    record["request"] = "Build a different portal"
    result = verify_solution(record)
    assert result["verified"] is False
