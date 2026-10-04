"""Explicit authorization boundary."""
from __future__ import annotations
ROLES={"owner":4,"admin":3,"operator":2,"viewer":1}
ACTIONS={"read":1,"search":1,"create_solution":2,"verify":3,"approve_deployment":4,"billing":3}
def authorize(role:str, action:str)->bool:
    if role not in ROLES or action not in ACTIONS: return False
    return ROLES[role] >= ACTIONS[action]
