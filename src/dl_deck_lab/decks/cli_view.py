from __future__ import annotations

import argparse
import re
import sys
import webbrowser
from pathlib import Path

import ygojson.database as ygodb

from dl_deck_lab.carddb.loader import load_database
from dl_deck_lab.decks.images import get_cached_image_path, to_data_uri
from dl_deck_lab.decks.render import CardRenderInfo, render_deck_html
from dl_deck_lab.decks.schema import Deck, load_decks

_CARD_TYPE_NAMES = {
    ygodb.CardType.MONSTER: "Monster",
    ygodb.CardType.SPELL: "Spell",
    ygodb.CardType.TRAP: "Trap",
}

_NO_IMAGE_DATA_URI = (
    "data:image/svg+xml;utf8,"
    "<svg xmlns='http://www.w3.org/2000/svg' width='343' height='500'>"
    "<rect width='100%' height='100%' fill='%23222'/>"
    "<text x='50%' y='50%' fill='%23888' font-size='20' text-anchor='middle'>no image</text>"
    "</svg>"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a saved deck as an HTML page (grouped/ordered like Duel Links' deck-edit screen) "
        "and open it in your default browser."
    )
    parser.add_argument("--decks", default="decks.json", help="Path to decks.json (default: ./decks.json)")
    parser.add_argument(
        "--name", help="Which deck to render (default: the only one, if decks.json has exactly one)"
    )
    parser.add_argument("--out", help="Output HTML path (default: <deck name, slugified>.html)")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use the already-cached card database instead of checking for updates",
    )
    parser.add_argument(
        "--no-open", action="store_true", help="Write the HTML file but don't open a browser"
    )
    return parser


def _select_deck(decks: list, name: str | None) -> Deck:
    if name is not None:
        for deck in decks:
            if deck.name == name:
                return deck
        available = ", ".join(d.name for d in decks)
        print(f"No deck named {name!r}. Available: {available}", file=sys.stderr)
        sys.exit(1)
    if len(decks) == 1:
        return decks[0]
    available = ", ".join(d.name for d in decks)
    print(f"Multiple decks found, pass --name to pick one: {available}", file=sys.stderr)
    sys.exit(1)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "deck"


def main() -> None:
    args = build_parser().parse_args()

    decks = load_decks(args.decks)
    if not decks:
        print(f"No decks found in {args.decks}", file=sys.stderr)
        sys.exit(1)
    deck = _select_deck(decks, args.name)

    db = load_database(offline=args.offline)
    cards_by_id = {str(c.id): c for c in db.cards}

    card_info = {}
    unique_ids = {c.card_id for c in deck.cards}
    for card_id in unique_ids:
        card = cards_by_id.get(card_id)
        if card is None:
            deck_name = next(c.name for c in deck.cards if c.card_id == card_id)
            print(f"{deck_name!r} (id {card_id}) not found in the card database, using a placeholder image", file=sys.stderr)
            name = deck_name
            card_type = "Other"
            image_uri = _NO_IMAGE_DATA_URI
        else:
            name = card.text[ygodb.Language.ENGLISH].name if ygodb.Language.ENGLISH in card.text else card_id
            card_type = _CARD_TYPE_NAMES.get(card.card_type, "Other")
            if card.images:
                image_path = get_cached_image_path(card_id, card.images[0].card_art)
                image_uri = to_data_uri(image_path)
            else:
                image_uri = _NO_IMAGE_DATA_URI
        card_info[card_id] = CardRenderInfo(name=name, card_type=card_type, image_data_uri=image_uri)

    html_content = render_deck_html(deck, card_info)

    out_path = Path(args.out) if args.out else Path(f"{_slugify(deck.name)}.html")
    out_path.write_text(html_content, encoding="utf-8")
    print(f"Wrote {out_path}")

    if not args.no_open:
        webbrowser.open(out_path.resolve().as_uri())


if __name__ == "__main__":
    main()
