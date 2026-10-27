from xparallel.identity_directory import get_founding_identity, list_founding_identities


def test_founding_keys_are_stable():
    assert [x["identity_key"] for x in list_founding_identities()] == [
        "oneai.core", "xparallel.verse"
    ]


def test_ecs_names_are_proposed_not_registered():
    for identity in list_founding_identities():
        assert identity["domain_status"] == "proposed_unregistered"
        assert identity["verification_status"] == "unverified"
        assert identity["endpoint_bindings"] == []


def test_lookup_is_defensive_and_unknown_returns_none():
    item = get_founding_identity("oneai.core")
    item["display_name"] = "changed"
    assert get_founding_identity("oneai.core")["display_name"] == "OneAI"
    assert get_founding_identity("missing") is None
