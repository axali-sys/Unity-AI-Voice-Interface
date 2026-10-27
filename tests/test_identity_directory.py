from xparallel.identity_directory import list_founding_identities, get_founding_identity


def test_founding_keys_are_stable():
    assert [x["identity_key"] for x in list_founding_identities()] == [
        "oneai.core", "xparallel.verse"
    ]


def test_ecs_names_are_proposed_not_registered():
    for identity in list_founding_identities():
        assert identity["domain_status"] == "proposed_unregistered"
        assert identity["verification_status"] == "unverified"
        assert identity["endpoint_bindings"] == []
        assert identity["preferred_domain_label"].endswith(".ecs")


def test_lookup_returns_copy_and_unknown_is_none():
    item = get_founding_identity("oneai.core")
    item["display_name"] = "changed"
    assert get_founding_identity("oneai.core")["display_name"] == "OneAI"
    assert get_founding_identity("missing") is None
