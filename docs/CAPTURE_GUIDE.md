# Capture guide

`dl-capture` only runs on Windows, natively (not WSL) — it needs to read
another Windows application's window, which WSL cannot do. If you normally
work from WSL, install a native Windows Python
(https://www.python.org/downloads/windows/) and run just this step from a
regular Windows terminal (PowerShell/cmd), inside this repo's path as seen
from Windows (e.g. `C:\Users\carja\Workspace\duel-links-deck-lab`).

```powershell
py -m venv .venv-windows
.venv-windows\Scripts\activate
pip install -e ".[capture]"
```

The `keyboard` package's global hotkey listener needs to run **as
Administrator** on Windows to catch keypresses while the game window has
focus — run your terminal elevated, or the capture hotkey silently won't
fire.

## 1. Run the capture session

```powershell
dl-capture
```

With Duel Links running, page to your collection/card-list screen. For each
page of cards you want captured, make sure it's fully loaded/settled, then
press `F9`. Press `F10` when you've gone through your whole collection.
Screenshots land in `.\captures\`.

### If the tool can't find the game window

The default `--window-title "Duel Links"` is a guess, not a confirmed title
from Konami. If you get `LookupError: No window found with title
containing 'Duel Links'`, list every open window's actual title:

```powershell
dl-capture --list-windows
```

Find the one that's the game (it may be titled just `"Yu-Gi-Oh!"`, or
something else entirely) and pass it explicitly:

```powershell
dl-capture --window-title "Yu-Gi-Oh"
```

If Duel Links doesn't show up in that list at all, it's likely running in a
fullscreen/exclusive display mode, which some window-enumeration APIs can't
see. Switch it to windowed or borderless-windowed mode in the game's display
settings and try again.

## 2. Calibrate a layout profile (one-time, per screen resolution/UI scale)

`dl-ocr` needs to know where on each screenshot the card name and copy-count
text sit. Because this depends on your window size and in-game UI scale,
there's no universal default — you calibrate it once against one of your own
screenshots:

1. Open one captured screenshot (e.g. `captures/20260101-120000-000000.png`)
   in any image viewer/editor that shows pixel coordinates (e.g. Paint, GIMP,
   even browser dev tools on a locally-opened image).
2. Find the pixel bounding box of the **first (top-left) card slot's name
   text**, and of its **copy-count badge** (the small "x2"/"x3" indicator).
3. Measure the slot's width and height (distance to the next slot's
   equivalent box, horizontally and vertically), and how many rows/columns
   are visible per page.
4. Write it to a JSON file, e.g. `my-layout.json`:

```json
{
  "name_box": { "left": 40, "top": 210, "right": 260, "bottom": 232 },
  "count_box": { "left": 220, "top": 232, "right": 260, "bottom": 250 },
  "slot_width": 280,
  "slot_height": 320,
  "rows": 3,
  "cols": 5
}
```

`name_box`/`count_box` are **absolute pixel coordinates in the screenshot**,
for the top-left slot only — not offsets relative to that slot's own corner.
`slot_boxes()` (see `src/dl_deck_lab/ocr/layout.py`) tiles that one
calibrated box across the full grid by adding `col * slot_width` and
`row * slot_height` to it.

5. If a page has a partially-filled last row (fewer cards than
   `rows * cols`), that's fine — empty slots OCR to blank text and are
   skipped automatically.

### Worked example

[`examples/layouts/deckbuilder-sidebar-2560x1440.json`](../examples/layouts/deckbuilder-sidebar-2560x1440.json)
is a real calibrated layout, measured against the Deck Edit screen's
compact "Card Inventory" sidebar at 2560x1440 (not a dedicated full-screen
card list — that sidebar was the only card-grid view found so far; if a
larger, dedicated browsing screen exists, prefer capturing that instead,
since bigger tiles with cleaner UI text will OCR more reliably than this
sidebar's tiny, card-art-embedded name text). It won't match your setup
exactly, but shows the shape of a working config, including a copy-count
box that deliberately overlaps into the next column because that's
genuinely where the game renders it.

If your card names are small and/or embedded in the card art rather than
a clean text label (as in that example), also see `--upscale` on `dl-ocr`
below — the default already enlarges each crop 4x before OCR, but you may
need more for a very compact grid.

## 3. Run OCR

From WSL, Linux, or Windows — doesn't matter:

```bash
dl-ocr --captures-dir captures --layout my-layout.json --out collection.json
```

Add `--upscale N` (default 4) to enlarge each crop further before OCR if
your card grid is small/compact.

Check the "low-confidence reads" printed to stderr — those are card names
Tesseract couldn't confidently match to a known Duel Links card, and were
skipped rather than guessed at. Fix them by hand in `collection.json`, or
recapture that specific screen if the text was genuinely unreadable.

## Requirements

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) must be
  installed and on your `PATH` (`pytesseract` is just a wrapper around the
  `tesseract` binary, it doesn't bundle it).
  - Windows: install via the [UB Mannheim
    build](https://github.com/UB-Mannheim/tesseract/wiki).
  - WSL/Linux: `sudo apt install tesseract-ocr`.
