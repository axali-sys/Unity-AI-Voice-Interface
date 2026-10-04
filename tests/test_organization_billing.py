from xparallel.organization import Member, normalize_org, can
from xparallel.billing_profile import billing_profile, invoice_request

def test_org_membership():
    m=Member("a","Acme Inc","owner")
    assert normalize_org("Acme Inc")=="acme-inc"
    assert can(m,"admin")
    assert not can(Member("v","acme","viewer"),"operator")

def test_billing_is_preview_only(monkeypatch):
    monkeypatch.setenv("XP_BILLING_EMAIL","billing@example.com")
    p=billing_profile("acme")
    assert p["email"]=="billing@example.com"
    assert p["payment_status"]=="not_connected"
    assert invoice_request("acme",[{"workspace_id":"acme","units":5}])["amount"]==5
