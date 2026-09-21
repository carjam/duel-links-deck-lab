from __future__ import annotations

import argparse

from dl_deck_lab.collection.schema import load_collection
from dl_deck_lab.decks.schema import load_decks
from dl_deck_lab.decks.validate import validate_deck


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check every deck in decks.json for structural legality (sizes, copy limits, ownership)."
    )
    parser.add_argument("--decks", default="decks.json", help="Path to decks.json (default: ./decks.json)")
    parser.add_argument(
        "--collection",
        default="collection.json",
        help="Path to collection.json, to also check you own enough copies (default: ./collection.json)",
    )
    parser.add_argument(
        "--skip-ownership",
        action="store_true",
        help="Only check deck size/copy-limit rules, not whether you own the cards",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    decks = load_decks(args.decks)
    owned_by_id = None
    if not args.skip_ownership:
        owned_by_id = {e.card_id: e.copies_owned for e in load_collection(args.collection)}

    any_failed = False
    for deck in decks:
        violations = validate_deck(deck, owned_by_id)
        status = "OK" if not violations else "FAILED"
        print(f"{deck.name}: {status}  (Main {deck.main_count()}, Extra {deck.extra_count()})")
        for v in violations:
            print(f"  - {v.message}")
        if violations:
            any_failed = True
        print()

    if any_failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
