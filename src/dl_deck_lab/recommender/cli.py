from __future__ import annotations

import argparse

from dl_deck_lab.carddb.loader import duel_links_cards, load_database
from dl_deck_lab.carddb.models import to_summary
from dl_deck_lab.collection.schema import load_collection
from dl_deck_lab.recommender.archetypes import build_archetype_index
from dl_deck_lab.recommender.completion import score_archetypes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Rank archetypes by how much of your Duel Links collection completes them."
    )
    parser.add_argument(
        "--collection",
        default="collection.json",
        help="Path to your collection.json (default: ./collection.json)",
    )
    parser.add_argument(
        "--top", type=int, default=10, help="How many archetypes to show (default: 10)"
    )
    parser.add_argument(
        "--min-members",
        type=int,
        default=3,
        help="Skip archetypes with fewer than this many obtainable cards (default: 3)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the already-cached card database instead of checking for updates",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    db = load_database(offline=args.offline)
    dl_cards = duel_links_cards(db)
    summaries = {s.id: s for s in (to_summary(c) for c in dl_cards)}
    card_names_by_id = {cid: s.name for cid, s in summaries.items()}

    archetypes = build_archetype_index(
        db, set(summaries.keys()), min_members=args.min_members
    )

    entries = load_collection(args.collection)
    owned_card_ids = {e.card_id for e in entries if e.copies_owned > 0}

    results = score_archetypes(
        owned_card_ids, archetypes, card_names_by_id, top_n=args.top
    )

    if not results:
        print("No archetypes matched (check --min-members or your collection file).")
        return

    for rank, r in enumerate(results, start=1):
        kind = "archetype" if r.is_named_archetype else "series"
        print(f"{rank:>2}. {r.archetype_name} ({kind})")
        print(f"    owned {r.owned_count}/{r.total_count} ({r.pct_owned:.0%})")
        if r.missing_card_names:
            print(f"    missing: {', '.join(r.missing_card_names)}")
        print()


if __name__ == "__main__":
    main()
