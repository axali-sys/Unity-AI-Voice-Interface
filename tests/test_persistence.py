from xparallel.persistence import SolutionRepository
from xparallel.solution import create_solution
from xparallel.graph import SolutionGraph

def test_repository_isolates_workspaces(tmp_path):
    repo = SolutionRepository(str(tmp_path / "xp.db"))
    solution = create_solution("Build a secure portal")
    node = SolutionGraph().add(solution)
    repo.put("alpha", node)
    assert repo.get("alpha", node["node_id"]) is not None
    assert repo.get("beta", node["node_id"]) is None
    repo.close()
