"""The decks.json format: named, buildable decklists distinct from collection.json.

collection.json tracks what you *own* and gets overwritten by every ``dl-ocr``
re-sync; a deck is a specific *build* from that collection and needs to
survive re-syncs independently, so it lives in its own file.

    [
      {
        "name": "Brave Neos HERO",
        "cards": [
          {"card_id": "<uuid>", "name": "Elemental HERO Stratos", "zone": "main", "quantity": 3},
          {"card_id": "<uuid>", "name": "Elemental HERO Brave Neos", "zone": "extra", "quantity": 3},
          ...
        ]
      },
      ...
    ]
"""

from __future__ import annotations

import dataclasses
import json
import typing


@dataclasses.dataclass
class DeckCard:
    card_id: str
    name: str
    zone: str
    """"main" or "extra"."""
    quantity: int


@dataclasses.dataclass
class Deck:
    name: str
    cards: typing.List[DeckCard]

    def main_count(self) -> int:
        return sum(c.quantity for c in self.cards if c.zone == "main")

    def extra_count(self) -> int:
        return sum(c.quantity for c in self.cards if c.zone == "extra")


def load_decks(path: str) -> typing.List[Deck]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [
        Deck(
            name=deck["name"],
            cards=[
                DeckCard(
                    card_id=c["card_id"], name=c["name"], zone=c["zone"], quantity=c["quantity"]
                )
                for c in deck["cards"]
            ],
        )
        for deck in raw
    ]


def save_decks(path: str, decks: typing.Iterable[Deck]) -> None:
    raw = [
        {"name": deck.name, "cards": [dataclasses.asdict(c) for c in deck.cards]}
        for deck in decks
    ]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2)
        f.write("\n")
