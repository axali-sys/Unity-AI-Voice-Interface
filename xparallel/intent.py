"""Structured human intent for XParallel V0.1."""
from dataclasses import dataclass, asdict


@dataclass
class Intent:
    goal: str
    environment: str = "sandbox"
    success_criteria: list[str] | None = None
    approval_required: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def parse_intent(query: str) -> Intent:
    goal = query.strip()
    if not goal:
        raise ValueError("intent_required")
    return Intent(goal=goal, success_criteria=["experiment completes without an unhandled error"])
