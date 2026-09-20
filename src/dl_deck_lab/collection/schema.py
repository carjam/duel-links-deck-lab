"""The collection.json format: what a player owns, keyed to YGOJSON card IDs.

This is the one file format that bridges the OCR step and the recommender
step, so it's kept dependency-free (plain dataclasses + json) and documented
here rather than inferred from either side.

    [
      {"card_id": "<ygojson uuid>", "name": "Pot of Greed", "copies_owned": 1},
      ...
    ]

``name`` is stored alongside ``card_id`` purely so the file stays readable/
diffable by a human; only ``card_id`` and ``copies_owned`` are load-bearing.
"""

from __future__ import annotations

import dataclasses
import json
import typing


@dataclasses.dataclass
class CollectionEntry:
    card_id: str
    name: str
    copies_owned: int


def load_collection(path: str) -> typing.List[CollectionEntry]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return [
        CollectionEntry(
            card_id=entry["card_id"],
            name=entry["name"],
            copies_owned=entry["copies_owned"],
        )
        for entry in raw
    ]


def save_collection(path: str, entries: typing.Iterable[CollectionEntry]) -> None:
    raw = [dataclasses.asdict(entry) for entry in entries]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, sort_keys=True)
        f.write("\n")
