from xparallel.graph import SolutionGraph
from xparallel.solution import create_solution


def test_graph_add_search_and_promote():
    graph = SolutionGraph()
    solution = create_solution("Build a secure payment API")
    record = graph.add(solution, tags=["payments", "security"])
    assert record["status"] == "candidate"
    assert graph.search("secure payment")
    promoted = graph.promote(solution["solution_id"])
    assert promoted["status"] == "verified"
    assert graph.summary()["verified"] == 1


def test_graph_fingerprint_changes_after_promotion():
    graph = SolutionGraph()
    solution = create_solution("Build an identity service")
    record = graph.add(solution)
    before = record["graph_fingerprint"]
    after = graph.promote(solution["solution_id"])["graph_fingerprint"]
    assert before != after
