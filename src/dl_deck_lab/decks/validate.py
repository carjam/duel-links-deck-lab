"""Structural deck-legality checks: sizes and copy limits.

This deliberately does NOT check the live Duel Links banlist (a card limited
to 1 or 2, or forbidden entirely, would still pass here) -- that's a known
gap, see docs/ROADMAP.md. It catches the mechanical rules that never change:
deck size, the standard 3-copies-per-name cap, and whether you actually own
enough copies of each card.
"""

from __future__ import annotations

import collections
import dataclasses
import typing

from dl_deck_lab.decks.schema import Deck

MAIN_DECK_MIN = 20
MAIN_DECK_MAX = 30
EXTRA_DECK_MAX = 8
MAX_COPIES_PER_CARD = 3


@dataclasses.dataclass(frozen=True)
class Violation:
    message: str


def validate_deck(
    deck: Deck, owned_copies_by_id: typing.Optional[typing.Dict[str, int]] = None
) -> typing.List[Violation]:
    """Returns every structural problem found; an empty list means the deck
    is legal to build in Duel Links (modulo the live banlist -- see module
    docstring). Pass ``owned_copies_by_id`` (card_id -> copies_owned, e.g.
    from collection.schema.load_collection) to also check you own enough
    copies of everything in the list.
    """
    violations = []

    main = deck.main_count()
    if not (MAIN_DECK_MIN <= main <= MAIN_DECK_MAX):
        violations.append(
            Violation(f"Main Deck has {main} cards, needs {MAIN_DECK_MIN}-{MAIN_DECK_MAX}")
        )

    extra = deck.extra_count()
    if extra > EXTRA_DECK_MAX:
        violations.append(Violation(f"Extra Deck has {extra} cards, max is {EXTRA_DECK_MAX}"))

    per_card_total: typing.Dict[str, int] = collections.defaultdict(int)
    for card in deck.cards:
        per_card_total[card.card_id] += card.quantity

    for card_id, total in per_card_total.items():
        name = next(c.name for c in deck.cards if c.card_id == card_id)
        if total > MAX_COPIES_PER_CARD:
            violations.append(
                Violation(f"{name}: {total} copies used, max is {MAX_COPIES_PER_CARD}")
            )

        if owned_copies_by_id is not None:
            owned = owned_copies_by_id.get(card_id, 0)
            if total > owned:
                violations.append(
                    Violation(f"{name}: deck uses {total}, but collection.json shows only {owned} owned")
                )

    return violations
