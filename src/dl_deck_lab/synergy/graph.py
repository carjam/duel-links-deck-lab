"""Builds a synergy graph from tagged cards and ranks payoff cards by support.

Deliberately pure -- operates on plain ``card_id -> Tags`` dicts, no DB or
file I/O -- so it's directly unit-testable with synthetic data.

Verified against the real 1,399-card collection, three times:

1. A naive connected-components clustering doesn't work: mill/discard is a
   broadly-shared resource (mechanically true in Yu-Gi-Oh -- any mill
   effect genuinely helps any GY-reliant payoff), so once a collection is
   large enough almost every miller and every payoff end up transitively
   connected into one meaningless mega-cluster (463 of 1,399 cards, in
   practice).
2. Ranking payoff cards by raw enabler count *without* restriction-awareness
   doesn't work either: every payoff showed the identical 160-enabler
   count, because untyped tags treat "any monster in GY" as interchangeable
   -- which is technically true but useless for ranking.
3. Adding a restriction (Type, Level cap, named archetype -- see
   ``tagging.py``) fixed the mechanics but not the ranking: restricted
   payoffs still showed ~140/160, because an *unrestricted* enabler
   legitimately satisfies a restricted payoff too (a generic mill really can
   send a Dragon), and most real mill/discard effects are unrestricted. That
   background support is real but not interesting -- almost every payoff
   has it. The genuinely interesting signal is an enabler whose OWN
   restriction exactly matches the payoff's, which is what actually
   differentiates payoffs -- so ``PayoffSupport`` reports that count
   (``specific_enabler_ids``) separately from the larger, less interesting
   generic-support count (``generic_enabler_ids``), and ranking sorts on the
   specific count first.
"""

from __future__ import annotations

import collections
import dataclasses
import typing

from dl_deck_lab.synergy.tagging import Signal, Tags
from dl_deck_lab.synergy.tags import FEEDS


@dataclasses.dataclass(frozen=True)
class Edge:
    card_a: str
    card_b: str
    output_tag: str
    """The tag on ``card_a`` that satisfies ``input_tag`` on ``card_b``."""
    input_tag: str
    restriction: typing.Optional[str]
    """The payoff's own restriction, if any (e.g. "dragon", "level_le_4") --
    None if the payoff itself is unrestricted."""
    is_specific_match: bool
    """True if the enabler's own restriction exactly matches the payoff's
    (the interesting case) rather than the enabler being a generic
    catch-all that happens to also cover this payoff."""


@dataclasses.dataclass(frozen=True)
class PayoffSupport:
    card_id: str
    """The payoff card (has a matching input tag)."""
    input_tag: str
    """Which of the payoff's input signals this support is for."""
    restriction: typing.Optional[str]
    specific_enabler_ids: typing.FrozenSet[str]
    """Enablers whose own restriction exactly matches this payoff's -- the
    interesting, differentiating support."""
    generic_enabler_ids: typing.FrozenSet[str]
    """Enablers that are unrestricted (or, if the payoff itself is
    unrestricted, any compatible enabler) -- real support, but present for
    almost every payoff, so not the primary ranking signal."""


def _signals_compatible(output: Signal, input_: Signal) -> bool:
    """An unrestricted payoff (wants "any monster") accepts any enabler. An
    unrestricted enabler (can send/target anything) can satisfy a restricted
    payoff too (the player just chooses a compatible card). Two restricted
    signals only match if they name the same restriction.
    """
    if input_.restriction is None or output.restriction is None:
        return True
    return output.restriction == input_.restriction


def build_edges(
    tags_by_id: typing.Dict[str, Tags],
    feeds: typing.Optional[typing.Dict[str, typing.FrozenSet[str]]] = None,
) -> typing.List[Edge]:
    """An edge for every (card whose output feeds another card's input) pair,
    in both directions -- if A feeds B AND B feeds A, that's two edges, both
    worth showing (it's a two-way engine, not a coincidence).

    ``feeds`` defaults to the real ``synergy.tags.FEEDS``; overridable for
    tests that need a synthetic, fully-isolated mapping (the real one
    legitimately has every producer tag feed every consumer tag, which
    makes it impossible to construct two guaranteed-disconnected groups
    from real tags alone).
    """
    feeds = FEEDS if feeds is None else feeds

    # A card with no outputs and no inputs can never form an edge -- skip it
    # before the O(n^2) pairwise comparison, since most of the ~7,700 Duel
    # Links-legal cards (and most of a 1,399-card collection) tag empty.
    relevant = {cid: tags for cid, tags in tags_by_id.items() if tags.outputs or tags.inputs}

    edges = []
    ids = list(relevant.keys())
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            edges.extend(_edges_between(a, relevant[a], b, relevant[b], feeds))
            edges.extend(_edges_between(b, relevant[b], a, relevant[a], feeds))
    return edges


def _edges_between(
    a: str, tags_a: Tags, b: str, tags_b: Tags, feeds: typing.Dict[str, typing.FrozenSet[str]]
) -> typing.List[Edge]:
    edges = []
    for output in tags_a.outputs:
        fed_input_tags = feeds.get(output.tag, frozenset())
        for input_ in tags_b.inputs:
            if input_.tag in fed_input_tags and _signals_compatible(output, input_):
                is_specific = (
                    input_.restriction is not None and output.restriction == input_.restriction
                )
                edges.append(
                    Edge(
                        card_a=a,
                        card_b=b,
                        output_tag=output.tag,
                        input_tag=input_.tag,
                        restriction=input_.restriction,
                        is_specific_match=is_specific,
                    )
                )
    return edges


def rank_payoff_support(edges: typing.List[Edge]) -> typing.List[PayoffSupport]:
    """Groups edges by payoff card (+ which input tag/restriction), ranked by
    number of *specific*-match enablers descending, then generic-match count
    as a tiebreak -- see module docstring for why raw/generic counts alone
    don't differentiate payoffs.
    """
    specific_by_payoff: typing.Dict[typing.Tuple[str, str, typing.Optional[str]], typing.Set[str]] = (
        collections.defaultdict(set)
    )
    generic_by_payoff: typing.Dict[typing.Tuple[str, str, typing.Optional[str]], typing.Set[str]] = (
        collections.defaultdict(set)
    )
    for edge in edges:
        key = (edge.card_b, edge.input_tag, edge.restriction)
        if edge.is_specific_match:
            specific_by_payoff[key].add(edge.card_a)
        else:
            generic_by_payoff[key].add(edge.card_a)

    all_keys = set(specific_by_payoff) | set(generic_by_payoff)
    results = [
        PayoffSupport(
            card_id=card_id,
            input_tag=input_tag,
            restriction=restriction,
            specific_enabler_ids=frozenset(specific_by_payoff.get((card_id, input_tag, restriction), set())),
            generic_enabler_ids=frozenset(generic_by_payoff.get((card_id, input_tag, restriction), set())),
        )
        for (card_id, input_tag, restriction) in all_keys
    ]
    results.sort(key=lambda r: (len(r.specific_enabler_ids), len(r.generic_enabler_ids)), reverse=True)
    return results
