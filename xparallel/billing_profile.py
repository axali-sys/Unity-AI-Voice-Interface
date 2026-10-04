"""Billing contact and invoice boundary. No payment capture occurs here."""
from __future__ import annotations
import os
from typing import Any
DEFAULT_CURRENCY="USD"
def billing_profile(organization_id:str)->dict[str,Any]:
    return {"organization_id":organization_id,"email":os.getenv("XP_BILLING_EMAIL",""),"currency":os.getenv("XP_BILLING_CURRENCY",DEFAULT_CURRENCY),"payment_status":"not_connected"}
def invoice_request(organization_id:str,events:list[dict[str,Any]],unit_price:float=1.0)->dict[str,Any]:
    profile=billing_profile(organization_id)
    units=sum(int(e.get("units",0)) for e in events if e.get("workspace_id")==organization_id)
    return {**profile,"units":units,"unit_price":unit_price,"amount":round(units*unit_price,2),"status":"invoice_preview"}
