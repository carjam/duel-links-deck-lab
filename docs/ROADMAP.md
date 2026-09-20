# Roadmap

## v1 (built)

- Manual-paging, hotkey-triggered screen capture (Windows-only).
- OCR + fuzzy name matching into `collection.json`.
- Archetype-completion recommender: rank archetypes/series by % owned, list
  what's missing.

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

## Other known gaps (not full v2, but worth doing before then)

- Duel Links banlist/restricted-count enforcement (`Legality.LIMIT1/2/3` per
  YGOJSON's `Format.DUELLINKS` legality data is available — just not consumed
  by the recommender yet).
- Skill card inventory (currently out of scope entirely — no capture/OCR
  support for the Skill selection screen).
- Packaging `dl-capture` as a standalone Windows `.exe` so non-Python users
  can use it.
