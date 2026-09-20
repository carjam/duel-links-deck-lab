from __future__ import annotations

import argparse
import glob
import os
import sys

from dl_deck_lab.carddb.loader import duel_links_cards, load_database
from dl_deck_lab.carddb.models import to_summary
from dl_deck_lab.collection.schema import CollectionEntry, save_collection
from dl_deck_lab.ocr.fuzzy_match import match_card_name
from dl_deck_lab.ocr.layout import load_layout_profile
from dl_deck_lab.ocr.parser import parse_screenshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Turn captured Duel Links collection screenshots into collection.json."
    )
    parser.add_argument(
        "--captures-dir",
        default="captures",
        help="Directory of screenshots produced by dl-capture (default: ./captures)",
    )
    parser.add_argument("--layout", required=True, help="Path to a calibrated layout JSON file")
    parser.add_argument(
        "--out", default="collection.json", help="Where to write the result (default: ./collection.json)"
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
    names_by_id = {s.id: s.name for s in (to_summary(c) for c in duel_links_cards(db))}

    layout = load_layout_profile(args.layout)
    screenshots = sorted(glob.glob(os.path.join(args.captures_dir, "*.png")))
    if not screenshots:
        print(f"No screenshots found in {args.captures_dir}", file=sys.stderr)
        sys.exit(1)

    owned: dict[str, CollectionEntry] = {}
    unmatched = []

    for path in screenshots:
        for reading in parse_screenshot(path, layout):
            match = match_card_name(reading.name_text, names_by_id)
            if not match.confident:
                unmatched.append((path, reading.name_text, match.matched_name, match.score))
                continue

            copies = reading.copies_owned if reading.copies_owned is not None else 0
            existing = owned.get(match.card_id)
            if existing is None or copies > existing.copies_owned:
                owned[match.card_id] = CollectionEntry(
                    card_id=match.card_id, name=match.matched_name, copies_owned=copies
                )

    save_collection(args.out, owned.values())
    print(f"Wrote {len(owned)} cards to {args.out}")

    if unmatched:
        print(f"\n{len(unmatched)} low-confidence reads skipped -- review manually:", file=sys.stderr)
        for path, ocr_text, guess, score in unmatched:
            print(f"  {path}: {ocr_text!r} (best guess: {guess!r}, score {score:.0f})", file=sys.stderr)


if __name__ == "__main__":
    main()
