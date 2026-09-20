"""Runs OCR over one captured collection screenshot, per-slot rather than whole-frame.

Cropping to the calibrated name/count regions before OCR avoids feeding
Tesseract card art, borders, and UI chrome it would otherwise have to ignore,
which is the single biggest accuracy lever available here.
"""

from __future__ import annotations

import dataclasses
import re
import typing

import pytesseract
from PIL import Image

from dl_deck_lab.ocr.layout import GridLayout


@dataclasses.dataclass(frozen=True)
class RawCardReading:
    name_text: str
    """Raw OCR output for the name region, whitespace-normalized but not matched to a card yet."""
    copies_owned: typing.Optional[int]
    """Parsed copy count, or None if the count text didn't OCR to a recognizable number."""


_DIGITS_RE = re.compile(r"\d+")


def _parse_count(raw_text: str) -> typing.Optional[int]:
    match = _DIGITS_RE.search(raw_text)
    return int(match.group()) if match else None


def parse_screenshot(image_path: str, layout: GridLayout) -> typing.List[RawCardReading]:
    image = Image.open(image_path)
    readings = []
    for name_box, count_box in layout.slot_boxes():
        name_crop = image.crop((name_box.left, name_box.top, name_box.right, name_box.bottom))
        count_crop = image.crop(
            (count_box.left, count_box.top, count_box.right, count_box.bottom)
        )

        name_text = pytesseract.image_to_string(name_crop).strip()
        if not name_text:
            # An empty slot (e.g. the last, partially-filled row of the grid).
            continue

        count_text = pytesseract.image_to_string(
            count_crop, config="--psm 7 -c tessedit_char_whitelist=0123456789x/"
        ).strip()

        readings.append(
            RawCardReading(name_text=name_text, copies_owned=_parse_count(count_text))
        )
    return readings
