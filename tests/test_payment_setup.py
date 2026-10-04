from xparallel.payment_setup import payment_request, payment_setup


def test_payment_setup_uses_masked_ecobank_destination():
    result = payment_setup("org-demo")
    assert result["provider"] == "Ecobank"
    assert result["account_display"] == "****2251"
    assert result["payment_capture"] == "disabled"


def test_payment_request_requires_positive_amount():
    result = payment_request("org-demo", 250000, reference="XP-250K")
    assert result["amount"] == 250000
    assert result["authorization_required"] is True
    assert result["status"] == "payment_request_pending"
