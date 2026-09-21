"""The current Duel Links banlist, as a small hand-maintained override file.

YGOJSON does NOT track this (verified: of 14,616 cards, only 1 has any
``Format.DUELLINKS`` legality entry at all -- the schema has the field, but
none of YGOJSON's data sources actually populate it for Duel Links). So
unlike everything else in ``carddb``, this can't be derived from the card
database automatically. It's a plain JSON file the user edits by hand when
Konami updates the list:

    {
      "Card Name": "forbidden",
      "Another Card": "limit1",
      "Yet Another": "limit2"
    }

Values match ``ygojson.database.Legality``'s names, lowercased
(forbidden/limit1/limit2/limit3/unlimited). Cards not listed are assumed
Unlimited (the standard 3-copy cap already enforced by ``validate.py``).
"""

from __future__ import annotations

import json
import typing

LIMIT_BY_LEGALITY = {
    "forbidden": 0,
    "limit1": 1,
    "limit2": 2,
    "limit3": 3,
    "unlimited": 3,
}


def load_banlist_limits(path: str, names_by_id: typing.Dict[str, str]) -> typing.Dict[str, int]:
    """Loads ``path`` and resolves each entry's card name to a card_id via
    ``names_by_id`` (id -> canonical English name, e.g. from
    ``carddb.models.to_summary``). Names not found are skipped with a
    warning printed to stderr, since a typo here should never crash a deck
    check -- it should just mean that one card isn't restricted this run.
    """
    import sys

    with open(path, encoding="utf-8") as f:
        raw: typing.Dict[str, str] = json.load(f)

    id_by_name = {name: cid for cid, name in names_by_id.items()}
    limits = {}
    for name, legality in raw.items():
        cid = id_by_name.get(name)
        if cid is None:
            print(f"banlist.json: {name!r} not found in the card database, skipping", file=sys.stderr)
            continue
        if legality not in LIMIT_BY_LEGALITY:
            print(f"banlist.json: {name!r} has unknown legality {legality!r}, skipping", file=sys.stderr)
            continue
        limits[cid] = LIMIT_BY_LEGALITY[legality]
    return limits
