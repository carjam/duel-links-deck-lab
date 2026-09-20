"""Builds an archetype/series -> member-card index from YGOJSON, scoped to Duel Links.

YGOJSON already tracks each card's archetype/series membership directly on
``Card.series`` (a :class:`ygojson.database.Series`), so this is just a
regrouping of that data rather than anything YGOJSON doesn't already know.
"""

from __future__ import annotations

import dataclasses
import typing

import ygojson.database as ygodb


@dataclasses.dataclass(frozen=True)
class Archetype:
    id: str
    name: str
    is_named_archetype: bool
    """True for a named archetype (cards that refer to each other by name),
    False for a broader thematic series. Both are useful completion targets."""
    member_card_ids: typing.Tuple[str, ...]
    """Only members that are actually obtainable in Duel Links."""


def build_archetype_index(
    db: ygodb.Database,
    duel_links_card_ids: typing.Set[str],
    *,
    min_members: int = 3,
) -> typing.List[Archetype]:
    """One :class:`Archetype` per YGOJSON series, restricted to Duel Links-legal
    members. Series with fewer than ``min_members`` obtainable cards are
    dropped -- they're not meaningful completion targets.
    """
    archetypes = []
    for series in db.series:
        if ygodb.Language.ENGLISH not in series.name:
            continue
        member_ids = tuple(
            str(card.id)
            for card in series.members
            if str(card.id) in duel_links_card_ids
        )
        if len(member_ids) < min_members:
            continue
        archetypes.append(
            Archetype(
                id=str(series.id),
                name=series.name[ygodb.Language.ENGLISH],
                is_named_archetype=series.archetype,
                member_card_ids=member_ids,
            )
        )
    return archetypes
