"""Read-only directory for proposed XParallel AI Verse founding identities."""
from copy import deepcopy

_IDENTITIES = [
    {"identity_key": "oneai.core", "display_name": "OneAI", "identity_type": "workspace",
     "ecosystem_role": "founding_workspace", "preferred_domain_label": "oneai.ecs",
     "domain_status": "proposed_unregistered", "verification_status": "unverified",
     "endpoint_bindings": [], "record_status": "proposed_founding_identity",
     "public_description": "The unified AI workspace and command center."},
    {"identity_key": "xparallel.verse", "display_name": "XParallel AI VERSE",
     "identity_type": "ecosystem_infrastructure", "ecosystem_role": "founding_infrastructure",
     "preferred_domain_label": "xparallel.ecs", "domain_status": "proposed_unregistered",
     "verification_status": "unverified", "endpoint_bindings": [],
     "record_status": "proposed_founding_identity",
     "public_description": "Interoperability and discovery infrastructure for compatible AI systems."},
]


def list_founding_identities():
    """Return proposed records; never implies domain registration or verification."""
    return deepcopy(_IDENTITIES)


def get_founding_identity(identity_key):
    """Return a proposed identity by stable key, or None."""
    key = str(identity_key or "").strip()
    for item in _IDENTITIES:
        if item["identity_key"] == key:
            return deepcopy(item)
    return None
