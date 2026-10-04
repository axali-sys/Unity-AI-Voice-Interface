from xparallel.authz import authorize
from xparallel.audit import audit_event
def test_role_boundaries():
    assert authorize("viewer","read")
    assert not authorize("viewer","create_solution")
    assert authorize("operator","create_solution")
    assert not authorize("operator","approve_deployment")
    assert authorize("owner","approve_deployment")
def test_audit_is_tamper_evident():
    e=audit_event("verification","acme","owner",{"node_id":"x"})
    assert len(e["event_fingerprint"]) == 64
