"""A plain-text decklist format, for hand-writing a deck without touching JSON.

    # Main Deck
    3 Elemental HERO Stratos
    3 Elemental HERO Neos

    # Extra Deck
    3 Elemental HERO Brave Neos
    2 Masked HERO Anki

A line starting with ``#`` is a section header if it mentions "main" or
"extra" (case-insensitive), otherwise a comment; either way it doesn't count
as a card. A card line is ``<quantity> <name>``; the quantity may be
omitted (defaults to 1). Blank lines are ignored. Zone defaults to "main"
until an "Extra" header is seen.
"""

from __future__ import annotations

import dataclasses
import typing


@dataclasses.dataclass(frozen=True)
class DecklistLine:
    quantity: int
    name: str
    zone: str


def parse_decklist_text(text: str) -> typing.List[DecklistLine]:
    zone = "main"
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            lowered = line.lower()
            if "extra" in lowered:
                zone = "extra"
            elif "main" in lowered:
                zone = "main"
            continue

        parts = line.split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            quantity, name = int(parts[0]), parts[1].strip()
        else:
            quantity, name = 1, line

        lines.append(DecklistLine(quantity=quantity, name=name, zone=zone))
    return lines
