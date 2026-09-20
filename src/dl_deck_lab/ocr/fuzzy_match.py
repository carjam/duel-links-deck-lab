"""Matches OCR'd (and therefore sometimes typo'd) card names to YGOJSON card IDs."""

from __future__ import annotations

import dataclasses
import typing

from rapidfuzz import fuzz, process, utils

DEFAULT_CONFIDENCE_THRESHOLD = 85.0
"""Below this rapidfuzz score (0-100), flag the match for manual review rather
than trusting it silently -- a wrong auto-match is worse than an unmatched
card, since it corrupts collection.json with a card the player doesn't own."""


@dataclasses.dataclass(frozen=True)
class MatchResult:
    ocr_text: str
    card_id: typing.Optional[str]
    matched_name: typing.Optional[str]
    score: float

    @property
    def confident(self) -> bool:
        return self.card_id is not None and self.score >= DEFAULT_CONFIDENCE_THRESHOLD


def match_card_name(
    ocr_text: str,
    known_names_by_id: typing.Dict[str, str],
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> MatchResult:
    """Fuzzy-match ``ocr_text`` against every known Duel Links card name.

    ``known_names_by_id`` maps card_id -> canonical English name, e.g. the
    output of ``carddb.models.to_summary`` over ``carddb.loader.duel_links_cards``.
    """
    id_by_name = {name: cid for cid, name in known_names_by_id.items()}
    # rapidfuzz scorers are case-sensitive by default, and OCR case is noisy
    # (verified: the same near-perfect OCR read scored 18 with mismatched
    # case vs 64 lowercased) -- always normalize case/punctuation before scoring.
    best = process.extractOne(
        ocr_text, id_by_name.keys(), scorer=fuzz.WRatio, processor=utils.default_process
    )

    if best is None:
        return MatchResult(ocr_text=ocr_text, card_id=None, matched_name=None, score=0.0)

    matched_name, score, _ = best
    card_id = id_by_name[matched_name] if score >= threshold else None
    return MatchResult(
        ocr_text=ocr_text,
        card_id=card_id,
        matched_name=matched_name,
        score=score,
    )


def top_candidates(
    ocr_text: str, known_names_by_id: typing.Dict[str, str], *, limit: int = 3
) -> typing.List[str]:
    """The ``limit`` closest known names to ``ocr_text``, for a human to pick from.

    Used when OCR quality is bad enough that no single match can be trusted
    automatically (see docs/ROADMAP.md's note on the deck-builder sidebar
    capture source): verified against real garbled OCR output that plain
    ``fuzz.ratio`` surfaces the correct name in its top 3 noticeably more
    often than ``fuzz.WRatio`` does, though neither scores it confidently
    enough to auto-accept. This exists to make manual review fast (pick
    from a short list while looking at your own screen), not to replace it.
    """
    id_by_name = {name: cid for cid, name in known_names_by_id.items()}
    return [
        name
        for name, _score, _ in process.extract(
            ocr_text, id_by_name.keys(), scorer=fuzz.ratio, processor=utils.default_process, limit=limit
        )
    ]
