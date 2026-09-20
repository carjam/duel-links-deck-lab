"""Runs OCR over one captured collection screenshot, per-slot rather than whole-frame.

Cropping to the calibrated name/count regions before OCR avoids feeding
Tesseract card art, borders, and UI chrome it would otherwise have to ignore,
which is the single biggest accuracy lever available here. The second
biggest lever, needed for compact UIs where a card's name is small stylized
text baked into the card art (as opposed to a clean UI label), is upscaling
each crop before OCR -- Tesseract is trained on document-scale text and
does much better on a 4x-upscaled+sharpened crop than on the tiny original.
"""

from __future__ import annotations

import dataclasses
import re
import typing

import pytesseract
from PIL import Image, ImageFilter, ImageOps

from dl_deck_lab.ocr.layout import GridLayout

DEFAULT_UPSCALE = 4
"""How much to enlarge each crop before OCR. Card-art-embedded name text (a
compact grid like Duel Links' deck-builder inventory sidebar) benefits from
this a lot; a dedicated full-screen list view with clean, larger UI text may
not need as much -- tune per capture source."""


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


def _preprocess_for_ocr(crop: Image.Image, *, upscale: int) -> Image.Image:
    grayscale = crop.convert("L")
    enlarged = grayscale.resize(
        (grayscale.width * upscale, grayscale.height * upscale), Image.LANCZOS
    )
    sharpened = enlarged.filter(ImageFilter.SHARPEN)
    return ImageOps.autocontrast(sharpened)


def parse_screenshot(
    image_path: str, layout: GridLayout, *, upscale: int = DEFAULT_UPSCALE
) -> typing.List[RawCardReading]:
    image = Image.open(image_path)
    readings = []
    for name_box, count_box in layout.slot_boxes():
        name_crop = _preprocess_for_ocr(
            image.crop((name_box.left, name_box.top, name_box.right, name_box.bottom)),
            upscale=upscale,
        )
        count_crop = _preprocess_for_ocr(
            image.crop((count_box.left, count_box.top, count_box.right, count_box.bottom)),
            upscale=upscale,
        )

        name_text = pytesseract.image_to_string(name_crop, config="--psm 7").strip()
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
