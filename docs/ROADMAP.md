# Roadmap

## v1 (built)

- Manual-paging, hotkey-triggered screen capture (Windows-only).
- OCR + fuzzy name matching into `collection.json`.
- Archetype-completion recommender: rank archetypes/series by % owned, list
  what's missing.
- Named decklists (`decks.json`) with structural legality checking
  (`dl-deck-check`) and a plain-text importer (`dl-deck-import`) — see
  `src/dl_deck_lab/decks/`.
- `dl-deck-view`: renders a saved deck as a self-contained HTML page
  (grouped/ordered like the in-game deck-edit screen) and opens it locally.

## v2: combo/synergy graph search

The v1 recommender only reasons about *named archetypes/series* as YGOJSON
already groups them. It has no idea that, say, a generic "special summon from
GY" monster combos with an unrelated archetype's GY-filling engine — that
kind of cross-archetype synergy isn't represented anywhere in YGOJSON's
schema, so it has to be derived from card effect text.

The intended v2 approach:

1. **Tag extraction**: parse each Duel Links-legal card's effect text
   (`CardText.effect` in YGOJSON) into a small set of mechanical tags —
   things like `searches`, `special-summons-from-gy`, `mills`,
   `banishes-for-cost`, `negates-activation`, etc. This is the hard part:
   either a hand-curated tag ruleset matched against effect text patterns, or
   an LLM-assisted first pass that a human reviews before trusting it.
2. **Synergy graph**: build a graph where cards are nodes and edges represent
   "card A's output tag feeds card B's input tag" (e.g. A mills, B has a
   GY-cost effect).
3. **Combo search over owned cards**: given your `collection.json`, search
   this graph restricted to cards you own, surfacing connected clusters —
   these are your candidate "engines", independent of whether they fall under
   a single named archetype.
4. **Ranking**: some notion of combo strength/consistency (e.g. how many
   copies you own of each piece, how many alternate paths into the same
   effect) rather than just raw connectivity.

This is a substantially bigger lift than v1 and deliberately deferred — v1
ships something genuinely useful (archetype completion) without needing to
solve card-effect NLP first.

## Known limitation: Tesseract OCR is not reliable on Duel Links' UI at any tested screen

Verified across two different in-game screens (the deck-builder's compact
"Card Inventory" sidebar, ~92px tiles, and the full-screen "Card Catalog"
browser, ~125px tiles): Tesseract + rapidfuzz matching against the ~14,500
Duel Links card name pool does **not** reliably resolve either card names or
copy-count digits, even after fixing real bugs found along the way
(`fuzz.WRatio` is case-sensitive by default and needs
`processor=rapidfuzz.utils.default_process`; forcing `--psm 7` on the name
crop measurably hurt accuracy vs. default page segmentation). The core
problem: correct OCR reads of garbled text score in the same 55-70 range as
coincidentally-similar wrong candidates, so no confidence threshold both
accepts true positives and rejects false positives — a wrong "confident"
match (e.g. one real test: `Junk Converter` OCR'd text matched `7 Colored
Fish` at a score above the default threshold) silently corrupts
`collection.json`, which is worse than not matching at all.

What *does* work: reading the same screenshots directly (by a human, or a
vision-capable model) and fuzzy-matching those clean transcriptions against
the real card database — typo-level noise resolves at 90%+ confidence
reliably, the same way `tests/test_fuzzy_match.py`'s OCR-typo case does.
`ocr.fuzzy_match.top_candidates()` exists for exactly this workflow: surface
a short list to confirm against, rather than trust a single low-quality
match. Until Tesseract accuracy improves (a higher-resolution capture source,
per-character contour analysis, or a different OCR engine entirely might
help — untested), treat `dl-ocr`'s automated matching as an assist for a
human/vision-model-driven transcription pass, not a hands-off pipeline.

## Other known gaps (not full v2, but worth doing before then)

- **Live Duel Links banlist**: verified this session that YGOJSON does NOT
  actually track it (`Format.DUELLINKS` legality is populated on essentially
  none of its 14,616 cards, despite the schema having the field) — the
  original plan to consume `Legality.LIMIT1/2/3` from there doesn't work.
  `dl-deck-check`/`dl-deck-import` instead accept an optional hand-maintained
  `banlist.json` (see `decks/banlist.py`) that you update yourself when
  Konami changes the list; there's no automated source for it.
- Skill card inventory (currently out of scope entirely — no capture/OCR
  support for the Skill selection screen).
- `dl_capture.spec`'s PyInstaller packaging (see `packaging/`) is **partially
  verified**: built and run on a real Windows machine, `--list-windows`
  printed real window titles correctly, confirming pygetwindow's hidden
  imports are sufficient. A full capture session (hotkey + screenshot,
  exercising `mss`/`keyboard`) hasn't been separately confirmed from the
  packaged binary yet.
