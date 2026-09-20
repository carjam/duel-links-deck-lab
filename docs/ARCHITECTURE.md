# Architecture

## Why capture is Windows-only and everything else isn't

The Duel Links Steam client is a native Windows GUI application. Capturing
its window contents requires the Win32 window/screen APIs (`pygetwindow`,
`mss`), which only work when Python is running natively on Windows. If you
develop from WSL (as this project's original author does), WSL cannot see or
capture another Windows process's window — there's no bridge for that, WSLg
notwithstanding (WSLg is for running *Linux* GUI apps, not capturing *Windows*
app windows).

So the package is split so only `dl_deck_lab.capture` needs to run under a
native Windows Python install:

- `dl_deck_lab.capture` — Windows-only. Finds the game window, listens for a
  capture hotkey, saves screenshots. Never imported by anything else in this
  project.
- `dl_deck_lab.ocr`, `dl_deck_lab.carddb`, `dl_deck_lab.collection`,
  `dl_deck_lab.recommender` — pure Python + Pillow/Tesseract/rapidfuzz/YGOJSON,
  no OS-specific dependencies. Run these from WSL, Linux, macOS, or Windows.

`pyproject.toml` reflects this: the Windows-only dependencies (`mss`,
`pygetwindow`, `keyboard`) are an optional `[capture]` extra, not a base
dependency. `dl_deck_lab/capture/cli.py` also refuses to run at all on a
non-Windows platform, with a clear error rather than a confusing import
failure deep in `pygetwindow`.

## Why capture never sends input to the game

`dl_deck_lab.capture` only *reacts* to a hotkey the player presses themselves
while manually paging through their own collection screens — it never
simulates clicks or scrolls inside the game client. This was an explicit
design choice to keep the tool firmly on the safe side of "reading pixels off
my own screen" rather than "automating input into someone else's game",
which is a materially different (and riskier, ToS-wise) thing to build.

## Data flow

```
(you, playing the game)
        |  press F9 per screen
        v
dl-capture  ---->  captures/*.png            [Windows-only]
                        |
                        v
dl-ocr  -------->  collection.json            [cross-platform]
   ^ (needs a calibrated layout.json,
      see CAPTURE_GUIDE.md)
   ^ (matches names against YGOJSON
      via carddb + fuzzy_match)
                        |
                        v
dl-recommend  --->  ranked archetype report   [cross-platform]
   ^ (needs YGOJSON's series/archetype data,
      via carddb + recommender/archetypes.py)
```

## Card data: YGOJSON

`dl_deck_lab.carddb.loader.load_database()` wraps
`ygojson.database.load_from_internet`, caching the individual+aggregate JSON
under `~/.cache/dl-deck-lab/ygojson/`. `duel_links_cards()` filters the full
database down to cards YGOJSON has confirmed are actually obtainable in Duel
Links (`Card.duel_links_rarity is not None`), which is more reliable than
checking Duel Links legality alone.

Archetype/series membership comes directly from YGOJSON's `Card.series`
field — `recommender/archetypes.py` just regroups that into
archetype/series -> member-card-ids, restricted to Duel Links-obtainable
members.
