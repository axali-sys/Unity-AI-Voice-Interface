from xparallel.audit_repository import AuditRepository

def test_audit_repository_round_trip():
    repo=AuditRepository(":memory:")
    event=repo.record("solution_created","acme","actor-1",{"solution_id":"xp-demo"})
    rows=repo.list("acme")
    assert rows[0]["event_fingerprint"] == event["event_fingerprint"]
    assert rows[0]["actor"] == "actor-1"
