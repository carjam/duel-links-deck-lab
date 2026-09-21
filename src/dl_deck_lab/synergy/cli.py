from __future__ import annotations

import argparse

from dl_deck_lab.carddb.loader import all_named_cards, load_database
from dl_deck_lab.carddb.models import to_summary
from dl_deck_lab.collection.schema import load_collection
from dl_deck_lab.synergy.graph import build_edges, rank_payoff_support
from dl_deck_lab.synergy.tagging import extract_tags


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank your GY-reliant payoff cards by how many distinct mill/discard enablers you "
        "own for them -- regardless of whether they share a named archetype."
    )
    parser.add_argument(
        "--collection",
        default="collection.json",
        help="Path to collection.json (default: ./collection.json)",
    )
    parser.add_argument(
        "--top", type=int, default=10, help="How many payoff cards to show (default: 10)"
    )
    parser.add_argument(
        "--sample", type=int, default=5, help="How many enabler names to list per payoff (default: 5)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the already-cached card database instead of checking for updates",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    owned = load_collection(args.collection)
    owned_ids = {e.card_id for e in owned if e.copies_owned > 0}

    db = load_database(offline=args.offline)
    summaries = {s.id: s for s in (to_summary(c) for c in all_named_cards(db)) if s.id in owned_ids}

    tags_by_id = {cid: extract_tags(s.effect_text) for cid, s in summaries.items()}
    edges = build_edges(tags_by_id)
    ranked = rank_payoff_support(edges)

    if not ranked:
        print("No GY-engine synergy found in your collection.")
        print(
            "This only looks for one specific pattern (mill/discard feeding a "
            "GY-reliant payoff) -- see docs/ROADMAP.md for what's not covered yet."
        )
        return

    for rank, support in enumerate(ranked[: args.top], start=1):
        name = summaries[support.card_id].name
        restriction_note = f", requires {support.restriction}" if support.restriction else ""
        print(f"{rank:>2}. {name} ({support.input_tag}{restriction_note})")
        if support.specific_enabler_ids:
            sample = sorted(summaries[eid].name for eid in support.specific_enabler_ids)[: args.sample]
            print(f"    {len(support.specific_enabler_ids)} enabler(s) matching this exact requirement: {', '.join(sample)}")
        if support.generic_enabler_ids:
            print(f"    + {len(support.generic_enabler_ids)} generic mill/discard effect(s) that also work")
        print()


if __name__ == "__main__":
    main()
