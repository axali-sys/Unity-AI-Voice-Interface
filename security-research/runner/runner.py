"""Local-only controlled research runner."""
from dataclasses import dataclass
from datetime import datetime, timezone

FORBIDDEN = {
    "credential_exfiltration",
    "third_party_access",
    "persistence",
    "service_disruption",
    "mass_enumeration",
}

@dataclass
class Test:
    test_id: str
    target: str
    data_type: str = "synthetic"
    action: str = "observation"

class SafetyGate:
    def __init__(self, authorized_targets, synthetic_only=True):
        self.authorized_targets = set(authorized_targets)
        self.synthetic_only = synthetic_only

    def approve(self, test: Test):
        if test.target not in self.authorized_targets:
            return False, "STOP: target outside authorized scope"
        if self.synthetic_only and test.data_type != "synthetic":
            return False, "STOP: non-synthetic data"
        if test.action in FORBIDDEN:
            return False, f"STOP: prohibited action: {test.action}"
        return True, "APPROVED"

def run():
    gate = SafetyGate(["local-synthetic-lab"])
    tests = [
        Test("AX-OPENAI-001", "local-synthetic-lab"),
        Test("AX-OPENAI-002", "local-synthetic-lab"),
        Test("AX-OPENAI-003", "local-synthetic-lab"),
    ]
    for test in tests:
        approved, reason = gate.approve(test)
        print({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_id": test.test_id,
            "status": "READY" if approved else "STOP",
            "reason": reason,
        })

if __name__ == "__main__":
    run()
