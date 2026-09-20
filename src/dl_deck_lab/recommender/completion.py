"""v1 recommender: rank archetypes by how much of them you already own.

This is deliberately simple -- no combo/synergy reasoning, no deck-legality
or banlist enforcement beyond "is this card obtainable in Duel Links" (see
docs/ROADMAP.md for what a v2 synergy-graph engine would add on top).
"""

from __future__ import annotations

import dataclasses
import typing

from dl_deck_lab.recommender.archetypes import Archetype


@dataclasses.dataclass(frozen=True)
class ArchetypeCompletion:
    archetype_name: str
    is_named_archetype: bool
    owned_count: int
    total_count: int
    pct_owned: float
    missing_card_names: typing.Tuple[str, ...]


def score_archetypes(
    owned_card_ids: typing.Set[str],
    archetypes: typing.Iterable[Archetype],
    card_names_by_id: typing.Dict[str, str],
    *,
    top_n: int = 10,
) -> typing.List[ArchetypeCompletion]:
    """Rank archetypes by (% owned, then absolute owned count) descending.

    The absolute-count tie-break only matters when pct_owned is equal, e.g.
    two fully-owned archetypes -- it prefers surfacing the larger one first.
    """
    scored = []
    for archetype in archetypes:
        owned = [cid for cid in archetype.member_card_ids if cid in owned_card_ids]
        missing = [cid for cid in archetype.member_card_ids if cid not in owned_card_ids]
        total = len(archetype.member_card_ids)
        if total == 0:
            continue
        scored.append(
            ArchetypeCompletion(
                archetype_name=archetype.name,
                is_named_archetype=archetype.is_named_archetype,
                owned_count=len(owned),
                total_count=total,
                pct_owned=len(owned) / total,
                missing_card_names=tuple(
                    card_names_by_id.get(cid, cid) for cid in missing
                ),
            )
        )

    scored.sort(key=lambda s: (s.pct_owned, s.owned_count), reverse=True)
    return scored[:top_n]
