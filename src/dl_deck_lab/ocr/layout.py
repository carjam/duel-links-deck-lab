"""Describes where card-name and copy-count text live on a captured collection screenshot.

There's no way to ship correct pixel coordinates for this sight unseen -- the
in-game collection grid's position depends on the player's window size and
UI scale. Instead, a layout is a small JSON file the user calibrates once
against their own screenshots (see docs/CAPTURE_GUIDE.md) and points
``dl-ocr`` at with ``--layout``.

The grid is assumed to be evenly-spaced rows/columns of identical card
slots, which matches Duel Links' collection screen; ``slot_boxes()``
generates every slot's bounding box from that one calibrated slot plus the
grid dimensions, so the user only has to measure one card, not every card on
the page.
"""

from __future__ import annotations

import dataclasses
import json
import typing


@dataclasses.dataclass(frozen=True)
class Box:
    left: int
    top: int
    right: int
    bottom: int


@dataclasses.dataclass(frozen=True)
class GridLayout:
    """One calibrated card slot, plus how many rows/columns of it tile the screen."""

    name_box: Box
    """Bounding box of the card name text, in absolute screenshot pixel
    coordinates, for the first (top-left, row=0/col=0) slot only. Every other
    slot's box is derived by shifting this one -- see `slot_boxes()`."""
    count_box: Box
    """Bounding box of the copy-count badge text, in absolute screenshot
    pixel coordinates, for the first slot only. Its box may legitimately
    extend past `slot_width`/into the next column if that's genuinely where
    the game renders it (e.g. an overlapping badge) -- `slot_boxes()` just
    shifts it by a consistent offset per column either way."""
    slot_width: int
    slot_height: int
    rows: int
    cols: int

    def slot_boxes(self) -> typing.Iterator[typing.Tuple[Box, Box]]:
        """Yields (name_box, count_box) for every slot on the page, in reading order."""
        for row in range(self.rows):
            for col in range(self.cols):
                dx = col * self.slot_width
                dy = row * self.slot_height
                yield (
                    _shift(self.name_box, dx, dy),
                    _shift(self.count_box, dx, dy),
                )


def _shift(box: Box, dx: int, dy: int) -> Box:
    return Box(box.left + dx, box.top + dy, box.right + dx, box.bottom + dy)


def load_layout_profile(path: str) -> GridLayout:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return GridLayout(
        name_box=Box(**raw["name_box"]),
        count_box=Box(**raw["count_box"]),
        slot_width=raw["slot_width"],
        slot_height=raw["slot_height"],
        rows=raw["rows"],
        cols=raw["cols"],
    )
