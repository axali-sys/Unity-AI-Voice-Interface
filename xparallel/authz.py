"""Explicit, deny-by-default authorization boundary for XParallel."""
from __future__ import annotations

ROLES = {"owner": 4, "admin": 3, "operator": 2, "viewer": 1}
ACTIONS = {
    "read": 1,
    "search": 1,
    "create_solution": 2,
    "verify": 3,
    "approve_deployment": 4,
    "billing": 3,
}


def authorize(role: str, action: str) -> bool:
    """Return whether a known role meets a known action's minimum level.

    Unknown values and non-string inputs are denied without raising. This is
    only a role-level policy primitive; callers must authenticate identity
    and apply resource/workspace-specific policy separately.
    """
    if not isinstance(role, str) or not isinstance(action, str):
        return False
    required_level = ACTIONS.get(action)
    role_level = ROLES.get(role)
    if required_level is None or role_level is None:
        return False
    return role_level >= required_level
