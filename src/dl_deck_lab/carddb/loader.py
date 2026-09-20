"""Loads and caches the YGOJSON card database, filtered to Duel Links.

YGOJSON (https://github.com/iconmaster5326/YGOJSON) is the canonical card data
source: card text, archetypes/series, and per-format legality including a
dedicated Duel Links rarity/legality signal. We never touch its raw JSON
directly -- we go through its Python API (``ygojson.database``) and just
narrow the result down to what this project needs.
"""

from __future__ import annotations

import os
import typing

import ygojson.database as ygodb

DEFAULT_CACHE_DIR = os.path.expanduser("~/.cache/dl-deck-lab/ygojson")


def load_database(
    cache_dir: str = DEFAULT_CACHE_DIR, *, offline: bool = False
) -> ygodb.Database:
    """Load the full YGOJSON database, downloading/refreshing it into ``cache_dir``.

    YGOJSON's ``load_from_internet`` only re-downloads when the server copy is
    newer, so it's safe to call this on every run. Pass ``offline=True`` to
    load whatever is already cached without touching the network (fails if
    nothing has been cached yet).
    """
    individuals_dir = os.path.join(cache_dir, "individual")
    aggregates_dir = os.path.join(cache_dir, "aggregate")
    os.makedirs(individuals_dir, exist_ok=True)
    os.makedirs(aggregates_dir, exist_ok=True)

    if offline:
        return ygodb.load_from_file(
            individuals_dir=individuals_dir, aggregates_dir=aggregates_dir
        )
    return ygodb.load_from_internet(
        individuals_dir=individuals_dir, aggregates_dir=aggregates_dir
    )


def duel_links_cards(db: ygodb.Database) -> typing.List[ygodb.Card]:
    """Cards YGOJSON has *confirmed* are obtainable in Duel Links.

    ``Card.duel_links_rarity`` is only set once YGOJSON's data sources have
    caught up to a given card actually being in Duel Links -- confirmed
    against a real screenshot, this lags behind reality: cards a player
    genuinely owns in-game can still have ``duel_links_rarity is None`` here.
    Good enough for the recommender's archetype-completion targets, but do
    NOT use this to filter what a card *name* is allowed to match against
    (see ``all_named_cards`` for that) -- it would silently reject real
    matches for cards YGOJSON just hasn't tagged yet.
    """
    return [card for card in db.cards if card.duel_links_rarity is not None and not card.illegal]


def all_named_cards(db: ygodb.Database) -> typing.List[ygodb.Card]:
    """Every card with an English name, regardless of Duel Links tagging.

    Use this as the match pool for identifying a card from OCR'd text or any
    other "what card is this" lookup -- restricting to ``duel_links_cards``
    there would miss real, owned cards that YGOJSON hasn't tagged yet.
    """
    return [card for card in db.cards if not card.illegal and ygodb.Language.ENGLISH in card.text]
