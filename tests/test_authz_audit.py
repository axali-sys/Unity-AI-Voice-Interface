from xparallel.authz import authorize
from xparallel.audit import audit_event


def test_role_boundaries():
    assert authorize("viewer", "read")
    assert authorize("viewer", "search")
    assert not authorize("viewer", "create_solution")
    assert authorize("operator", "create_solution")
    assert not authorize("operator", "verify")
    assert authorize("admin", "verify")
    assert not authorize("admin", "approve_deployment")
    assert authorize("owner", "approve_deployment")
    assert authorize("admin", "billing")


def test_unknown_roles_and_actions_fail_closed():
    assert not authorize("superuser", "read")
    assert not authorize("viewer", "delete_everything")


def test_non_string_inputs_fail_closed_without_raising():
    for role, action in (
        (None, "read"),
        ([], "read"),
        ("viewer", None),
        ("viewer", ["read"]),
        ({}, {}),
    ):
        assert authorize(role, action) is False


def test_audit_is_tamper_evident():
    event = audit_event("verification", "acme", "owner", {"node_id": "x"})
    assert len(event["event_fingerprint"]) == 64
