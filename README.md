# Duel Links Deck Lab

A collection tracker, deck builder, and combo finder for Yu-Gi-Oh Duel
Links, built on top of the [YGOJSON](https://github.com/iconmaster5326/YGOJSON)
card database. Everything after "capture" runs anywhere (Linux/macOS/WSL/Windows).

Duel Links has no official way to export your collection, and its built-in
auto-deck-builder just fills an archetype shell from whatever you own — it
doesn't tell you which archetypes you're closest to completing, whether a
deck is actually legal to play, or where a non-obvious combo is hiding across
cards that don't share an archetype name. This project covers that pipeline
end to end:

1. **Capture** — screenshot your in-game collection screens (Windows/Steam
   only, see below).
2. **OCR** — turn those screenshots into a `collection.json` of card IDs and
   copy counts, matched against YGOJSON's card database.
3. **Recommend** — rank every Duel Links archetype/series by how much of it
   you already own, and list exactly what's missing.
4. **Build** — save a specific deck build as `decks.json` and check it's
   actually legal to play: Main/Extra Deck size, the 3-copies-per-card cap,
   and whether you own enough copies of everything in it.
5. **View** — render a saved deck as a self-contained HTML page, grouped and
   ordered like Duel Links' own deck-edit screen, and open it in your
   browser.
6. **Find synergies** — surface cross-archetype combos your collection
   supports that a named-archetype recommender can't see (still an early,
   approximate first pass — see step 6 below and `docs/ROADMAP.md`).

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for why capture is
Windows-only while everything else runs anywhere, and
[`docs/ROADMAP.md`](docs/ROADMAP.md) for what's deliberately not built yet
and the real dead-ends/fixes found along the way for each piece.

## What's solid vs. still rough

Worth knowing before you rely on any of this:

| Piece | Status |
|---|---|
| Capture (`dl-capture`) | Works; `.exe` packaging partially verified (see `packaging/`) |
| OCR (`dl-ocr`) | **Not reliable** — verified Tesseract can't accurately read either screen tested; treat as an assist for manual/vision-model transcription, not automation (see `docs/ROADMAP.md`) |
| Recommend (`dl-recommend`) | Works, straightforward archetype-completion math |
| Deck build/check/view (`dl-deck-*`) | Works; no live banlist source, hand-maintained `banlist.json` only |
| Synergy (`dl-synergy`) | Early — verified against real examples (see below) but not yet fully vetted; regex-approximate by design |

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

### 5. View a deck

```bash
dl-deck-view
```

Renders the deck as a single HTML file, grouped and ordered the way
Duel Links' own deck-edit screen shows it (Main Deck as Monsters, then
Spells, then Traps; Extra Deck below), each unique card shown once with a
copy-count badge, and opens it in your default browser. Card art is
downloaded once and cached (`~/.cache/dl-deck-lab/card-images/`), then
embedded directly into the HTML — the file is self-contained, safe to move
or share. Pass `--name` if `decks.json` has more than one deck, or
`--no-open` to just write the file.

### 6. Find synergy clusters across your whole collection

```bash
dl-synergy --top 15
```

```
 1. Cyberdark Dragon (wants_gy_fodder, requires dragon)
    1 enabler(s) matching this exact requirement: Darkflare Dragon
    + 135 generic mill/discard effect(s) that also work
```

Archetype completion (`dl-recommend`) only sees named archetypes. This looks
for a specific cross-archetype pattern instead: a card that mills or
discards feeding a card whose effect needs something in the GY — restricted
by Type/Level/named-archetype where the card text specifies one, so e.g.
"Darkflare Dragon → Cyberdark Dragon" (a real, non-obvious Dragon-specific
combo) ranks above generic "any mill helps any GY effect" noise. Approximate
by design (regex over effect text, same honesty as the OCR module) and
scoped to GY-engine synergies only — see `docs/ROADMAP.md` for what it
doesn't cover.

## Known limitations (v1)

- No *live* Duel Links banlist data — YGOJSON doesn't track it. `dl-deck-check`
  enforces the standard 3-copy cap and deck sizes always, and a hand-maintained
  `banlist.json` on top if you keep one current; without it, a card currently
  Limited to 1 in-game would still pass.
- No Skill card inventory tracking.
- `dl-synergy` only looks for one pattern (GY-engine synergies) — not the
  full combo/synergy space (see `docs/ROADMAP.md`'s v2 notes).

## Contributing

Card data issues belong upstream at
[YGOJSON](https://github.com/iconmaster5326/YGOJSON/issues), not here. Issues
with capture/OCR accuracy, the recommender, or anything else in this repo are
welcome.

## License

MIT — see [`LICENSE`](LICENSE).
