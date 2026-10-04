from xparallel.billing import invoice_preview, usage_event
from xparallel.workspace import workspace_context

def test_workspace_context_and_billing():
    ctx = workspace_context({"workspace_id": "Acme Corp", "actor": "owner"})
    assert ctx["workspace_id"] == "Acme-Corp"
    event = usage_event("solution_created", ctx["workspace_id"])
    preview = invoice_preview(ctx["workspace_id"], [event])
    assert preview["units"] == 1
    assert preview["estimated_total"] == 1.0
