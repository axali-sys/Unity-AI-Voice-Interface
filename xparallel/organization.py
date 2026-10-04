"""Organization and membership model for tenant-scoped XParallel access."""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
import re
ROLES={"owner":4,"admin":3,"operator":2,"viewer":1}
@dataclass(frozen=True)
class Member:
    actor_id:str
    organization_id:str
    role:str
    def __post_init__(self):
        if not self.actor_id or not self.organization_id or self.role not in ROLES:
            raise ValueError("invalid_member")
def normalize_org(value:str)->str:
    value=re.sub(r"[^a-z0-9_-]+","-",str(value or "").strip().lower()).strip("-")
    return value[:64] or "default"
def organization_fingerprint(organization_id:str)->str:
    return sha256(normalize_org(organization_id).encode()).hexdigest()
def can(member:Member,action_role:str)->bool:
    return member.role in ROLES and action_role in ROLES and ROLES[member.role]>=ROLES[action_role]
