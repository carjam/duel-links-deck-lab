from __future__ import annotations

import argparse
import os
import sys

from dl_deck_lab.carddb.loader import all_named_cards, load_database
from dl_deck_lab.carddb.models import to_summary
from dl_deck_lab.collection.schema import load_collection
from dl_deck_lab.decks.banlist import load_banlist_limits
from dl_deck_lab.decks.decklist_text import parse_decklist_text
from dl_deck_lab.decks.schema import Deck, DeckCard, load_decks, save_decks
from dl_deck_lab.decks.validate import validate_deck
from dl_deck_lab.ocr.fuzzy_match import match_card_name, top_candidates


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Turn a plain-text decklist into a named deck in decks.json."
    )
    parser.add_argument("--input", required=True, help="Path to a plain-text decklist (see decklist_text.py)")
    parser.add_argument("--name", required=True, help="Name to save this deck under")
    parser.add_argument("--out", default="decks.json", help="Path to decks.json (default: ./decks.json)")
    parser.add_argument(
        "--collection",
        default="collection.json",
        help="Path to collection.json, to report ownership issues (default: ./collection.json)",
    )
    parser.add_argument(
        "--banlist",
        default="banlist.json",
        help="Path to a hand-maintained banlist file (default: ./banlist.json, skipped if absent)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=90.0,
        help="Minimum fuzzy-match confidence to accept a typed card name (default: 90 -- "
        "higher than OCR's default since these are hand-typed, not machine-read)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the already-cached card database instead of checking for updates",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    with open(args.input, encoding="utf-8") as f:
        lines = parse_decklist_text(f.read())
    if not lines:
        print(f"No card lines found in {args.input}", file=sys.stderr)
        sys.exit(1)

    db = load_database(offline=args.offline)
    names_by_id = {s.id: s.name for s in (to_summary(c) for c in all_named_cards(db))}

    deck_cards = []
    unresolved = []
    for line in lines:
        match = match_card_name(line.name, names_by_id, threshold=args.threshold)
        if not match.confident:
            unresolved.append(line)
            continue
        deck_cards.append(
            DeckCard(card_id=match.card_id, name=match.matched_name, zone=line.zone, quantity=line.quantity)
        )

    if unresolved:
        print(f"{len(unresolved)} line(s) could not be confidently matched, skipped:", file=sys.stderr)
        for line in unresolved:
            candidates = top_candidates(line.name, names_by_id, limit=3)
            print(f"  {line.name!r} -- did you mean: {', '.join(candidates)}?", file=sys.stderr)

    deck = Deck(name=args.name, cards=deck_cards)

    existing = load_decks(args.out) if os.path.exists(args.out) else []
    existing = [d for d in existing if d.name != deck.name]
    save_decks(args.out, existing + [deck])
    print(f"Saved {len(deck_cards)} card(s) to {deck.name!r} in {args.out}")

    owned_by_id = {e.card_id: e.copies_owned for e in load_collection(args.collection)} if os.path.exists(args.collection) else None
    banlist_limits = None
    if os.path.exists(args.banlist):
        banlist_limits = load_banlist_limits(args.banlist, names_by_id)

    violations = validate_deck(deck, owned_by_id, banlist_limits)
    print(f"\n{deck.name}: {'OK' if not violations else 'FAILED'}  (Main {deck.main_count()}, Extra {deck.extra_count()})")
    for v in violations:
        print(f"  - {v.message}")


if __name__ == "__main__":
    main()
