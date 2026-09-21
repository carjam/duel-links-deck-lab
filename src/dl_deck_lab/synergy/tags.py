"""The tag vocabulary and which output tags satisfy which input tags.

Scoped deliberately narrow for this first pass: GY-engine synergies (a card
that fills the Graveyard feeding a card that benefits from GY contents) --
the single highest-signal, most reliably-detectable cross-archetype pattern
found when sampling real card text (see docs/ROADMAP.md). Not every Yu-Gi-Oh
mechanic; more tags/pairings can be added the same way later without
changing the graph-building logic.
"""

from __future__ import annotations

import typing

# Output tags: what a card's effect actively DOES.
MILLS_FROM_DECK = "mills_from_deck"
DISCARDS_FROM_HAND = "discards_from_hand"
SPECIAL_SUMMONS_FROM_GY = "special_summons_from_gy"
SPECIAL_SUMMONS_FROM_HAND = "special_summons_from_hand"
SEARCHES_DECK = "searches_deck"
BANISHES_FROM_GY = "banishes_from_gy"
EQUIPS_FROM_GY = "equips_from_gy"
RETURNS_TO_HAND = "returns_to_hand"
DESTROYS_MONSTER = "destroys_monster"
DESTROYS_SPELL_TRAP = "destroys_spell_trap"
NEGATES = "negates"
DRAWS_OR_DIGS = "draws_or_digs"

# Input tags: what a card's effect benefits from already being true.
WANTS_GY_FODDER = "wants_gy_fodder"
"""Needs a monster already sitting in the GY to Special Summon or equip."""
GY_COUNT_RELIANT = "gy_count_reliant"
"""Effect scales with how many/which cards are in the GY (e.g. an ATK boost
per named card in the GYs)."""

# Which output tags satisfy which input tags. Deliberately explicit and
# small -- "any shared tag counts as synergy" would false-positive on things
# like two unrelated search effects "matching" each other.
#
# Only genuine GY-*fillers* are producers here. special_summons_from_gy and
# banishes_from_gy are GY *consumers* (a card that does one of those should
# itself carry the wants_gy_fodder INPUT tag, not appear as a FEEDS key) --
# it's the same card's own effect needing fodder that some other card fills.
FEEDS: typing.Dict[str, typing.FrozenSet[str]] = {
    MILLS_FROM_DECK: frozenset({WANTS_GY_FODDER, GY_COUNT_RELIANT}),
    DISCARDS_FROM_HAND: frozenset({WANTS_GY_FODDER, GY_COUNT_RELIANT}),
}
