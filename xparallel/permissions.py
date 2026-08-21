"""Human-authority boundary for XParallel V0.1."""


ACTIONS = {
    "read": "READ",
    "suggest": "SUGGEST",
    "execute": "EXECUTE",
    "confirm": "CONFIRM",
    "override": "OVERRIDE",
}


def approval_required(action: str) -> bool:
    return action.upper() in {"EXECUTE", "CONFIRM"}
