"""Structural deck-legality checks: sizes, copy limits, and (optionally) the banlist.

Deck size and the standard 3-copies-per-name cap never change and are always
enforced. The *live* Duel Links banlist is a different matter -- YGOJSON
doesn't track it (see ``banlist.py``'s docstring), so checking it here is
opt-in: pass ``banlist_limits`` (from ``banlist.load_banlist_limits``) if you
maintain that file, and a card limited below 3 gets checked against its real
limit instead of the generic cap.
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
    deck: Deck,
    owned_copies_by_id: typing.Optional[typing.Dict[str, int]] = None,
    banlist_limits: typing.Optional[typing.Dict[str, int]] = None,
) -> typing.List[Violation]:
    """Returns every structural problem found; an empty list means the deck
    is legal to build. Pass ``owned_copies_by_id`` (card_id -> copies_owned,
    e.g. from collection.schema.load_collection) to also check you own
    enough copies of everything in the list. Pass ``banlist_limits``
    (card_id -> max copies, from ``banlist.load_banlist_limits``) to also
    check against a hand-maintained banlist -- without it, every card is
    only checked against the generic 3-copy cap.
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

        banlist_limit = (banlist_limits or {}).get(card_id)
        effective_max = MAX_COPIES_PER_CARD if banlist_limit is None else banlist_limit
        if total > effective_max:
            reason = "banlist" if banlist_limit is not None else "the standard cap"
            violations.append(
                Violation(f"{name}: {total} copies used, max is {effective_max} ({reason})")
            )

        if owned_copies_by_id is not None:
            owned = owned_copies_by_id.get(card_id, 0)
            if total > owned:
                violations.append(
                    Violation(f"{name}: deck uses {total}, but collection.json shows only {owned} owned")
                )

    return violations
