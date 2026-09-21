# Duel Links Deck Lab

A collection tracker and archetype-completion recommender for Yu-Gi-Oh Duel
Links, built on top of the [YGOJSON](https://github.com/iconmaster5326/YGOJSON)
card database.

Duel Links' built-in auto-deck-builder just fills an archetype shell from
whatever you own — it doesn't tell you which archetypes you're closest to
completing, or exactly what's missing. There's also no official way to export
your collection. This project does both:

1. **Capture** — screenshot your in-game collection screens (Windows/Steam
   only, see below).
2. **OCR** — turn those screenshots into a `collection.json` of card IDs and
   copy counts, matched against YGOJSON's card database.
3. **Recommend** — rank every Duel Links archetype/series by how much of it
   you already own, and list exactly what's missing.
4. **Build** — save a specific deck build as `decks.json` and check it's
   actually legal to play: Main/Extra Deck size, the 3-copies-per-card cap,
   and whether you own enough copies of everything in it.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for why capture is
Windows-only while everything else runs anywhere, and
[`docs/ROADMAP.md`](docs/ROADMAP.md) for what's deliberately not built yet
(most notably: true combo/synergy search, not just archetype completion).

## Quickstart

```bash
pip install -e .
```

### 1. Capture your collection (native Windows Python only — not WSL)

```bash
pip install -e ".[capture]"
dl-capture
```

Page through your in-game collection screens yourself; press `F9` on each
screen to capture it, `F10` when done. Screenshots land in `./captures/`.
See [`docs/CAPTURE_GUIDE.md`](docs/CAPTURE_GUIDE.md) — you'll need to
calibrate a layout profile once for your screen resolution before this can
be parsed.

### 2. Turn captures into a collection file (anywhere, including WSL)

```bash
dl-ocr --layout my-layout.json
```

Writes `collection.json`. Low-confidence OCR reads are skipped and printed
for manual review rather than guessed at.

### 3. Get archetype recommendations

```bash
dl-recommend --top 10
```

```
 1. Blue-Eyes (archetype)
    owned 6/9 (67%)
    missing: Blue-Eyes Spirit Dragon, Blue-Eyes Twin Burst Dragon, Sage with Eyes of Blue

 2. Fire Kings (archetype)
    owned 4/7 (57%)
    missing: ...
```

### 4. Save and validate a deck

`decks.json` holds named decklists (a specific build), separate from
`collection.json` (what you own overall) since a re-sync shouldn't erase your
saved builds. Write a plain-text decklist (see
[`examples/decklists/brave-neos-hero.decklist`](examples/decklists/brave-neos-hero.decklist))
and import it:

```bash
dl-deck-import --input my-deck.decklist --name "My Deck"
```

This resolves each line's card name against the real card database (fuzzy
matching handles small typos, same as `dl-ocr`), saves it into `decks.json`,
and validates it immediately. To re-check a saved deck later:

```bash
dl-deck-check
```

```
Brave Neos HERO: OK  (Main 30, Extra 8)
```

Checks Main/Extra Deck size, the 3-copies-per-card cap, and (unless
`--skip-ownership`) that `collection.json` actually shows enough copies of
everything used. If you maintain a `banlist.json` (see
[`src/dl_deck_lab/decks/banlist.py`](src/dl_deck_lab/decks/banlist.py) —
YGOJSON doesn't track Duel Links' live banlist, so this has to be
hand-maintained), it's also checked against that.

## Known limitations (v1)

- No *live* Duel Links banlist data — YGOJSON doesn't track it. `dl-deck-check`
  enforces the standard 3-copy cap and deck sizes always, and a hand-maintained
  `banlist.json` on top if you keep one current; without it, a card currently
  Limited to 1 in-game would still pass.
- No Skill card inventory tracking.
- Recommends by archetype completion only, not by actual combo/synergy
  potential across your whole collection (see `docs/ROADMAP.md`).

## Contributing

Card data issues belong upstream at
[YGOJSON](https://github.com/iconmaster5326/YGOJSON/issues), not here. Issues
with capture/OCR accuracy, the recommender, or anything else in this repo are
welcome.

## License

MIT — see [`LICENSE`](LICENSE).
