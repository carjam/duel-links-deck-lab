"""Thin, stable views over the YGOJSON schema fields this project actually uses.

Keeping these separate from ``ygojson.database.Card`` means the rest of the
codebase (OCR matching, the recommender) doesn't need to know about YGOJSON's
full schema, and a YGOJSON upgrade only requires changes here.

Note: archetype/series membership is deliberately NOT exposed here. YGOJSON's
published data populates ``Series.members`` (archetype -> its cards) but not
the reverse ``Card.series`` link, so per-card archetype lookup isn't
available without scanning every series -- see
``recommender.archetypes.build_archetype_index``, which does that scan once
against ``Database.series`` directly instead.
"""

from __future__ import annotations

import dataclasses

import ygojson.database as ygodb


@dataclasses.dataclass(frozen=True)
class CardSummary:
    id: str
    name: str
    duel_links_legal: bool


def to_summary(card: ygodb.Card) -> CardSummary:
    text = card.text.get(ygodb.Language.ENGLISH)
    name = text.name if text is not None else str(card.id)

    duel_links_legality = card.legality.get(ygodb.Format.DUELLINKS)
    duel_links_legal = (
        duel_links_legality is not None
        and duel_links_legality.legality != ygodb.Legality.FORBIDDEN
    )

    return CardSummary(
        id=str(card.id),
        name=name,
        duel_links_legal=duel_links_legal,
    )
