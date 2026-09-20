from dl_deck_lab.recommender.archetypes import Archetype
from dl_deck_lab.recommender.completion import score_archetypes


def make_archetype(name, member_ids, is_named=True):
    return Archetype(
        id=name.lower().replace(" ", "-"),
        name=name,
        is_named_archetype=is_named,
        member_card_ids=tuple(member_ids),
    )


CARD_NAMES = {
    "c1": "Blue-Eyes White Dragon",
    "c2": "Blue-Eyes Toon Dragon",
    "c3": "Blue-Eyes Ultimate Dragon",
    "c4": "Red-Eyes Black Dragon",
    "c5": "Red-Eyes Darkness Metal Dragon",
}


def test_ranks_by_percent_owned_descending():
    archetypes = [
        make_archetype("Blue-Eyes", ["c1", "c2", "c3"]),
        make_archetype("Red-Eyes", ["c4", "c5"]),
    ]
    owned = {"c1", "c4", "c5"}  # Blue-Eyes 1/3, Red-Eyes 2/2

    results = score_archetypes(owned, archetypes, CARD_NAMES, top_n=10)

    assert [r.archetype_name for r in results] == ["Red-Eyes", "Blue-Eyes"]
    assert results[0].pct_owned == 1.0
    assert results[1].pct_owned == 1 / 3


def test_missing_card_names_are_resolved_from_ids():
    archetypes = [make_archetype("Blue-Eyes", ["c1", "c2", "c3"])]
    owned = {"c1"}

    [result] = score_archetypes(owned, archetypes, CARD_NAMES, top_n=10)

    assert result.owned_count == 1
    assert result.total_count == 3
    assert set(result.missing_card_names) == {
        "Blue-Eyes Toon Dragon",
        "Blue-Eyes Ultimate Dragon",
    }


def test_top_n_limits_results():
    archetypes = [
        make_archetype("A", ["c1"]),
        make_archetype("B", ["c2"]),
        make_archetype("C", ["c3"]),
    ]
    results = score_archetypes({"c1", "c2", "c3"}, archetypes, CARD_NAMES, top_n=2)
    assert len(results) == 2
