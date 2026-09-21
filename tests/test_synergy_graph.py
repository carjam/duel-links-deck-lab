from dl_deck_lab.synergy.graph import build_edges, rank_payoff_support
from dl_deck_lab.synergy.tagging import Signal, Tags
from dl_deck_lab.synergy.tags import GY_COUNT_RELIANT, MILLS_FROM_DECK, WANTS_GY_FODDER


def test_unrestricted_output_and_input_creates_an_edge():
    tags_by_id = {
        "miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, None)})),
    }
    edges = build_edges(tags_by_id)
    assert len(edges) == 1
    assert edges[0].card_a == "miller"
    assert edges[0].card_b == "payoff"
    assert edges[0].output_tag == MILLS_FROM_DECK
    assert edges[0].input_tag == WANTS_GY_FODDER
    assert edges[0].restriction is None


def test_unrelated_tags_create_no_edge():
    tags_by_id = {
        "a": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "b": Tags(outputs=frozenset(), inputs=frozenset()),  # no input tags at all
    }
    assert build_edges(tags_by_id) == []


def test_matching_restrictions_are_compatible():
    tags_by_id = {
        "dragon_miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, "dragon")}), inputs=frozenset()),
        "dragon_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, "dragon")})),
    }
    edges = build_edges(tags_by_id)
    assert len(edges) == 1
    assert edges[0].restriction == "dragon"


def test_mismatched_restrictions_are_not_compatible():
    tags_by_id = {
        "dragon_miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, "dragon")}), inputs=frozenset()),
        "warrior_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, "warrior")})),
    }
    assert build_edges(tags_by_id) == []


def test_unrestricted_enabler_still_feeds_a_restricted_payoff():
    # An unrestricted mill can send *any* monster, including a matching one --
    # a generic miller should still support a type-restricted payoff.
    tags_by_id = {
        "generic_miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "dragon_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, "dragon")})),
    }
    edges = build_edges(tags_by_id)
    assert len(edges) == 1
    # Reported restriction reflects the payoff's own need, not the enabler's.
    assert edges[0].restriction == "dragon"


def test_restricted_enabler_still_feeds_an_unrestricted_payoff_without_mislabeling_it():
    # A Dragon-specific mill can still satisfy a payoff that doesn't care
    # about type -- and the edge must report the payoff's restriction (None),
    # not the enabler's ("dragon"), or ranking would fragment this payoff
    # into bogus per-enabler-restriction sub-groups (a real bug caught this
    # session: an unrestricted payoff was getting split by whichever
    # enabler's own restriction happened to feed it).
    tags_by_id = {
        "dragon_miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, "dragon")}), inputs=frozenset()),
        "generic_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, None)})),
    }
    edges = build_edges(tags_by_id)
    assert len(edges) == 1
    assert edges[0].restriction is None


def test_bidirectional_feed_produces_edges_both_ways():
    tags_by_id = {
        "a": Tags(
            outputs=frozenset({Signal(MILLS_FROM_DECK, None)}),
            inputs=frozenset({Signal(GY_COUNT_RELIANT, None)}),
        ),
        "b": Tags(
            outputs=frozenset({Signal(MILLS_FROM_DECK, None)}),
            inputs=frozenset({Signal(GY_COUNT_RELIANT, None)}),
        ),
    }
    edges = build_edges(tags_by_id)
    directions = {(e.card_a, e.card_b) for e in edges}
    assert directions == {("a", "b"), ("b", "a")}


def test_payoff_with_no_enablers_never_appears():
    tags_by_id = {
        "lonely_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, None)})),
    }
    edges = build_edges(tags_by_id)
    assert rank_payoff_support(edges) == []


def test_ranks_payoffs_by_distinct_enabler_count_descending():
    tags_by_id = {
        "miller_1": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "miller_2": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "miller_3": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "well_supported_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, None)})),
        "under_supported_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(GY_COUNT_RELIANT, None)})),
    }
    # Both payoffs are fed by all 3 millers (MILLS_FROM_DECK feeds both input
    # tags per the real FEEDS mapping) -- so this instead tests that a payoff
    # with fewer real enablers in the collection ranks lower, by removing one
    # miller's connection to the under-supported payoff via a custom feeds map.
    feeds = {MILLS_FROM_DECK: frozenset({WANTS_GY_FODDER})}  # doesn't feed GY_COUNT_RELIANT here
    edges = build_edges(tags_by_id, feeds=feeds)

    ranked = rank_payoff_support(edges)

    assert len(ranked) == 1
    assert ranked[0].card_id == "well_supported_payoff"
    # All three millers here are unrestricted, so this counts as generic
    # support (real, but not the differentiating "exact match" signal).
    assert ranked[0].generic_enabler_ids == {"miller_1", "miller_2", "miller_3"}
    assert ranked[0].specific_enabler_ids == frozenset()


def test_specific_match_ranks_above_larger_generic_only_match():
    tags_by_id = {
        "dragon_miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, "dragon")}), inputs=frozenset()),
        "dragon_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, "dragon")})),
        "generic_miller_1": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "generic_miller_2": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "generic_miller_3": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "generic_payoff": Tags(outputs=frozenset(), inputs=frozenset({Signal(WANTS_GY_FODDER, None)})),
    }
    # generic_payoff has 3 generic enablers (a bigger raw number) but 0
    # exact-restriction matches; dragon_payoff has only 1 enabler total, but
    # it's an exact match -- the interesting, differentiating case, so it
    # must still rank first despite the smaller raw count.
    edges = build_edges(tags_by_id)
    ranked = rank_payoff_support(edges)

    payoff_order = [r.card_id for r in ranked if r.input_tag == WANTS_GY_FODDER]
    assert payoff_order.index("dragon_payoff") < payoff_order.index("generic_payoff")


def test_payoff_with_both_input_tags_gets_one_entry_per_tag():
    tags_by_id = {
        "miller": Tags(outputs=frozenset({Signal(MILLS_FROM_DECK, None)}), inputs=frozenset()),
        "dual_payoff": Tags(
            outputs=frozenset(),
            inputs=frozenset({Signal(WANTS_GY_FODDER, None), Signal(GY_COUNT_RELIANT, None)}),
        ),
    }
    edges = build_edges(tags_by_id)
    ranked = rank_payoff_support(edges)

    input_tags = {r.input_tag for r in ranked if r.card_id == "dual_payoff"}
    assert input_tags == {WANTS_GY_FODDER, GY_COUNT_RELIANT}
