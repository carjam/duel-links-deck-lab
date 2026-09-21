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

## v2: combo/synergy graph search (GY-engine slice built; rest still open)

The v1 recommender only reasons about *named archetypes/series* as YGOJSON
already groups them. It has no idea that, say, a generic "special summon from
GY" monster combos with an unrelated archetype's GY-filling engine — that
kind of cross-archetype synergy isn't represented anywhere in YGOJSON's
schema, so it has to be derived from card effect text.

**Built** (`src/dl_deck_lab/synergy/`, `dl-synergy`): the GY-engine slice —
a card that mills/discards feeding a card whose effect needs something in
the GY. Three real design problems surfaced and were fixed by actually
running it against the real 1,399-card collection, not just unit tests:

1. **Connected-components clustering doesn't work.** Mill/discard is a
   broadly-shared resource (mechanically true -- any mill helps any
   GY-reliant payoff), so a large enough collection transitively merges
   almost every miller and payoff into one meaningless mega-cluster (463 of
   1,399 cards, in practice). Fixed by ranking *payoff* cards by enabler
   count instead of clustering.
2. **Untyped tags don't differentiate payoffs.** Every payoff showed the
   identical enabler count, because "any monster in GY" was treated as one
   interchangeable bucket. Fixed by giving GY-related tags an optional
   *restriction* (a Type like "dragon", a Level cap like "level_le_4", or a
   named archetype like "red-eyes"), extracted from the same effect text,
   and only counting an enabler as a genuine match when its own restriction
   is compatible with the payoff's.
3. **Restriction-awareness alone still wasn't enough** — restricted payoffs
   still showed ~140/160, because an *unrestricted* enabler legitimately
   satisfies a restricted payoff too (a generic mill really can send a
   Dragon), so generic support drowned out the interesting signal. Fixed by
   reporting exact-restriction matches (`specific_enabler_ids`) separately
   from generic catch-all support (`generic_enabler_ids`), and ranking on
   the specific count first. Verified against real output:
   "Darkflare Dragon → Cyberdark Dragon" (a real, non-obvious Dragon-specific
   combo, confirmed against both cards' actual effect text) now correctly
   outranks generic noise.

Also found and fixed two regex false-positives along the way, both from the
same root cause (a sentence packing an unrelated condition and effect
together): a bare `deck` match didn't distinguish "Extra Deck" from the Main
Deck (false-positived Mask Change as a mill), and a GY mention in a trigger
*condition* leaked into an unrelated effect clause (false-positived Masked
HERO Dian as summoning from GY when it summons from the Deck) — fixed by
only matching within the text after a sentence's last `:`, since official
templating is overwhelmingly "[condition]: [effect]".

**Not built yet** — the rest of the original v2 sketch:

1. More mechanical tags beyond the GY-engine pattern (equip synergies
   without a GY source, negation chains, protection/immunity stacking,
   etc.) — same tagging approach, just more patterns.
2. Combo **strength** ranking beyond "how many distinct enablers" — e.g.
   weighting by copies owned, or by how many alternate paths into the same
   effect exist.
3. This only reasons about DL-legal cards' effect text as YGOJSON has it;
   still approximate by design (regex, not real parsing) — same honesty as
   the OCR module, prefer under-tagging over inventing a false combo.

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
