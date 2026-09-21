"""Renders a Deck as a single self-contained HTML page.

Cards are grouped and ordered the way Duel Links' own deck-edit screen shows
them: Main Deck as Monsters, then Spells, then Traps, each shown once with a
copy-count badge (not repeated per copy); Extra Deck as its own section
below. Deliberately decoupled from image-fetching/DB lookups (see
``images.py`` and ``cli_view.py`` for that) so this stays a pure,
easily-testable string-building function.
"""

from __future__ import annotations

import collections
import dataclasses
import html
import typing

from dl_deck_lab.decks.schema import Deck

CARD_TYPE_ORDER = ["Monster", "Spell", "Trap", "Other"]


@dataclasses.dataclass(frozen=True)
class CardRenderInfo:
    name: str
    card_type: str
    """One of "Monster", "Spell", "Trap", "Other"."""
    image_data_uri: str


def _aggregate_quantities(cards: typing.Iterable) -> typing.Dict[str, int]:
    totals: typing.Dict[str, int] = collections.defaultdict(int)
    for card in cards:
        totals[card.card_id] += card.quantity
    return totals


def _tile_html(card_id: str, quantity: int, info: CardRenderInfo) -> str:
    name = html.escape(info.name)
    return f"""
      <div class="card-tile">
        <div class="art-wrap">
          <img src="{info.image_data_uri}" alt="{name}" loading="lazy">
          <span class="copies">&times;{quantity}</span>
        </div>
        <h3>{name}</h3>
      </div>"""


def _section_html(title: str, card_ids_and_qty: typing.List[typing.Tuple[str, int]], card_info: typing.Dict[str, CardRenderInfo]) -> str:
    if not card_ids_and_qty:
        return ""
    tiles = "".join(_tile_html(cid, qty, card_info[cid]) for cid, qty in card_ids_and_qty)
    count = sum(qty for _, qty in card_ids_and_qty)
    return f"""
    <section>
      <div class="section-head">
        <h2>{html.escape(title)}</h2>
        <span class="count-pill">{count} card{'s' if count != 1 else ''}</span>
      </div>
      <div class="card-grid">{tiles}
      </div>
    </section>"""


def render_deck_html(deck: Deck, card_info: typing.Dict[str, CardRenderInfo]) -> str:
    """``card_info`` must have an entry for every card_id used in ``deck``."""
    main_ids = {c.card_id for c in deck.cards if c.zone == "main"}
    extra_ids = {c.card_id for c in deck.cards if c.zone == "extra"}

    main_totals = _aggregate_quantities(c for c in deck.cards if c.zone == "main")
    extra_totals = _aggregate_quantities(c for c in deck.cards if c.zone == "extra")

    def sorted_group(ids: typing.Set[str], totals: typing.Dict[str, int]) -> typing.List[typing.Tuple[str, int]]:
        return sorted(((cid, totals[cid]) for cid in ids), key=lambda pair: card_info[pair[0]].name)

    main_sections = ""
    for card_type in CARD_TYPE_ORDER:
        ids_of_type = {cid for cid in main_ids if card_info[cid].card_type == card_type}
        main_sections += _section_html(
            f"Main Deck — {card_type}s" if card_type != "Other" else "Main Deck — Other",
            sorted_group(ids_of_type, main_totals),
            card_info,
        )

    extra_section = _section_html("Extra Deck", sorted_group(extra_ids, extra_totals), card_info)

    main_count = sum(main_totals.values())
    extra_count = sum(extra_totals.values())
    deck_name = html.escape(deck.name)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{deck_name}</title>
<style>
  :root {{
    --bg: #0b1220;
    --surface: #16213a;
    --text: #e8edf5;
    --text-dim: #93a1b8;
    --accent: #52d6e8;
    --border: rgba(255, 255, 255, 0.10);
    --shadow: 0 1px 2px rgba(0,0,0,.4), 0 4px 12px rgba(0,0,0,.3);
  }}
  * {{ box-sizing: border-box; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    margin: 0;
    padding: 28px 20px 64px;
  }}
  .page {{ max-width: 1080px; margin-inline: auto; display: flex; flex-direction: column; gap: 36px; }}
  header h1 {{ font-size: clamp(24px, 4vw, 36px); margin: 0 0 6px; }}
  header .stats {{ color: var(--text-dim); font-size: 14px; }}
  .section-head {{ display: flex; align-items: baseline; justify-content: space-between; gap: 12px; margin-bottom: 14px; }}
  .section-head h2 {{ font-size: 18px; margin: 0; }}
  .count-pill {{
    font-family: ui-monospace, monospace;
    font-size: 12px;
    color: var(--text-dim);
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 3px 10px;
    border-radius: 999px;
  }}
  .card-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 14px; }}
  .card-tile {{ display: flex; flex-direction: column; gap: 6px; }}
  .art-wrap {{ position: relative; border-radius: 8px; overflow: hidden; border: 1px solid var(--border); box-shadow: var(--shadow); background: var(--surface); }}
  .art-wrap img {{ display: block; width: 100%; aspect-ratio: 686 / 1000; object-fit: cover; }}
  .copies {{
    position: absolute; top: 5px; right: 5px;
    background: rgba(11,18,32,.82); color: #fff;
    font-family: ui-monospace, monospace; font-size: 11px;
    padding: 2px 6px; border-radius: 999px; border: 1px solid rgba(255,255,255,.18);
  }}
  .card-tile h3 {{ font-size: 12.5px; font-weight: 500; line-height: 1.3; margin: 0; }}
</style>
</head>
<body>
  <div class="page">
    <header>
      <h1>{deck_name}</h1>
      <div class="stats">Main Deck {main_count} &middot; Extra Deck {extra_count}</div>
    </header>
    {main_sections}
    {extra_section}
  </div>
</body>
</html>
"""
