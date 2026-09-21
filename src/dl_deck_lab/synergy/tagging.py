"""Regex-based tagging of a card's effect text into the synergy.tags vocabulary.

Approximate by design, same honesty as the OCR module: official Yu-Gi-Oh
card text is heavily templated ("Send 1 ... from your Deck to the GY",
"Special Summon ... from your Graveyard"), which makes keyword/regex
matching real signal -- but it will still miss unusually-worded effects
(false negatives) and can't perfectly disambiguate every clause. Patterns
are checked per-*sentence* (split on periods only, not every punctuation
mark) specifically because splitting on ';'/':' too breaks real card text
where a target clause and its effect clause are joined by those and need to
stay together for the pattern to see both halves (verified against real
samples, e.g. Junk Synchron's "...monster in your GY; Special Summon that
target..." -- splitting on ';' would separate "GY" from "Special Summon"
and miss the match entirely).

Most tags check for their required words appearing anywhere in the same
sentence (real card text rarely coincidentally combines these specific word
pairs across unrelated clauses). One pair needs tighter, *proximity-bound*
matching: "destroy" verified to false-positive on "Destroy Spells/Traps ...
up to the number of HERO monsters you control" -- both "destroy" and
"monsters" are in that sentence, but the sentence destroys Spells/Traps, not
monsters ("monsters" there is just a counting reference many words later).

GY-related tags also carry an optional *restriction* (a named archetype like
"Red-Eyes", a Type like "Dragon", or a Level cap like "level_le_4") --
verified necessary against the real collection: without it, EVERY GY-mill
effect satisfies EVERY GY-reliant payoff identically (mechanically true --
any mill can send any monster -- but useless for ranking, since it produced
the exact same "160 enablers" count for every single payoff card). A
restricted payoff (e.g. "Special Summon 1 Dragon monster from your GY") is
only fed by an enabler that's either unrestricted (can send/target anything)
or shares the same restriction -- see graph.py's compatibility check.

Prefer under-tagging (missing a real synergy) over over-tagging (inventing
one from an unrelated clause) -- a missed cluster is a quiet gap, a false
cluster actively misleads someone building a deck around it.
"""

from __future__ import annotations

import dataclasses
import re
import typing

from dl_deck_lab.synergy import tags as t

_SENTENCE_SPLIT_RE = re.compile(r"\.")

_GY = r"\b(gy|gys|graveyard|graveyards)\b"
# Negative lookbehind excludes "Extra Deck" -- verified necessary against a
# real false positive: Mask Change's "...send it to the GY... from your
# Extra Deck..." matched MILLS_FROM_DECK's bare "deck" check even though the
# Extra Deck mention has nothing to do with the (unrelated) GY send.
_DECK = r"(?<!extra )\bdeck\b"
_HAND = r"\bhand\b"
_DESTROY_NEAR_TARGET = r"\bdestroy(s|ing|ed)?\b(?:\W+\w+){{0,4}}\W+{target}"

# Real YGO monster Types, longest/most-specific phrasing first so e.g.
# "winged beast" and "beast-warrior" are matched as themselves rather than
# just "beast". Not exhaustive (a few obscure Types omitted) -- a missed
# Type just falls through to "no restriction found", which is safe.
_TYPES = [
    "winged beast", "beast-warrior", "sea serpent", "divine-beast",
    "dragon", "warrior", "spellcaster", "zombie", "machine", "aqua",
    "pyro", "rock", "fairy", "insect", "dinosaur", "reptile", "fish",
    "plant", "wyrm", "cyberse", "psychic", "thunder", "fiend", "beast",
]
_TYPE_RE = re.compile(r"\b(" + "|".join(_TYPES) + r")\b\s+monster")
_NAMED_RE = re.compile(r'"([a-z][\w\- ]*?)"\s+monster')
_LEVEL_RE = re.compile(r"\blevel (\d+) or (lower|higher)\b")


@dataclasses.dataclass(frozen=True)
class Signal:
    tag: str
    restriction: typing.Optional[str] = None
    """None means unrestricted (matches/produces any monster). Otherwise a
    normalized key: a lowercased quoted archetype name, a Type name, or
    "level_le_N"/"level_ge_N" -- see module docstring."""


@dataclasses.dataclass(frozen=True)
class Tags:
    outputs: typing.FrozenSet[Signal] = frozenset()
    inputs: typing.FrozenSet[Signal] = frozenset()


def _extract_restriction(sentence: str) -> typing.Optional[str]:
    """Most-specific-first: a named archetype beats a Type beats a Level cap."""
    named = _NAMED_RE.search(sentence)
    if named:
        return named.group(1)
    typed = _TYPE_RE.search(sentence)
    if typed:
        return typed.group(1)
    leveled = _LEVEL_RE.search(sentence)
    if leveled:
        direction = "le" if leveled.group(2) == "lower" else "ge"
        return f"level_{direction}_{leveled.group(1)}"
    return None


# Each tag needs ALL of its listed regexes to match somewhere in the same
# sentence (order-independent -- real card text puts the target/condition
# clause first as often as the action verb, e.g. "...in your GY; Special
# Summon that target...", GY *before* the verb, so a single ordered pattern
# would miss that common case).
_OUTPUT_REQUIREMENTS: typing.List[typing.Tuple[str, typing.List["re.Pattern[str]"], bool]] = [
    # (tag, required patterns, whether this tag carries a GY-target restriction)
    (t.MILLS_FROM_DECK, [re.compile(r"\b(send|mill)(s|ing|ed)?\b"), re.compile(_DECK), re.compile(_GY)], True),
    (t.DISCARDS_FROM_HAND, [re.compile(r"\bdiscard(s|ing|ed)?\b")], False),
    (t.SPECIAL_SUMMONS_FROM_GY, [re.compile(r"\bspecial\b.*\bsummon(s|ed)?\b"), re.compile(_GY)], True),
    (t.SPECIAL_SUMMONS_FROM_HAND, [re.compile(r"\bspecial\b.*\bsummon(s|ed)?\b"), re.compile(_HAND)], False),
    (t.SEARCHES_DECK, [re.compile(r"\badd(s|ing|ed)?\b"), re.compile(_DECK), re.compile(_HAND)], False),
    (t.BANISHES_FROM_GY, [re.compile(r"\bbanish(es|ing|ed)?\b"), re.compile(_GY)], True),
    (t.EQUIPS_FROM_GY, [re.compile(r"\bequip(s|ping|ped)?\b"), re.compile(_GY)], True),
    (t.RETURNS_TO_HAND, [re.compile(r"\breturn(s|ing|ed)?\b"), re.compile(_HAND)], False),
    # These two use a single proximity-bound pattern instead of two independent
    # ones -- see module docstring for why plain co-occurrence false-positived here.
    (t.DESTROYS_SPELL_TRAP, [re.compile(_DESTROY_NEAR_TARGET.format(target=r"(spell|trap)s?\b"))], False),
    (t.DESTROYS_MONSTER, [re.compile(_DESTROY_NEAR_TARGET.format(target=r"monsters?\b"))], False),
    (t.NEGATES, [re.compile(r"\bnegate(s|d)?\b")], False),
    (t.DRAWS_OR_DIGS, [re.compile(r"\bdraws?\b")], False),
]

_INPUT_REQUIREMENTS: typing.List[typing.Tuple[str, typing.List["re.Pattern[str]"], bool]] = [
    (t.GY_COUNT_RELIANT, [re.compile(r"\bfor (every|each)\b"), re.compile(_GY)], True),
]

# Having one of these OUTPUT tags implies the card also NEEDS gy fodder to
# use its own effect -- derived rather than separately pattern-matched,
# since "wants_gy_fodder" isn't itself a phrase that appears in card text.
# The implied WANTS_GY_FODDER inherits the same sentence's restriction (e.g.
# Cyberdark Edge's "Level 3 or lower Dragon monster" target).
_IMPLIES_WANTS_GY_FODDER = frozenset({t.SPECIAL_SUMMONS_FROM_GY, t.EQUIPS_FROM_GY})


def extract_tags(effect_text: typing.Optional[str]) -> Tags:
    if not effect_text:
        return Tags()

    sentences = [s.strip().lower() for s in _SENTENCE_SPLIT_RE.split(effect_text) if s.strip()]

    outputs: typing.Set[Signal] = set()
    inputs: typing.Set[Signal] = set()
    for raw_sentence in sentences:
        # Official card text overwhelmingly follows a "[condition]: [effect]"
        # structure; only the segment after the *last* colon is the actual
        # effect being performed. Verified necessary against a real false
        # positive: Masked HERO Dian's "...destroys a monster and sends it to
        # the GY: You can Special Summon 1 ... monster from your Deck" has
        # "GY" only in the unrelated condition clause -- matching against the
        # whole sentence wrongly tagged this as special_summons_from_gy, when
        # it actually summons from the Deck. (No effect on sentences with no
        # colon, or where the colon separates a target clause from its own
        # effect within the same instruction, e.g. Junk Synchron's "...You can
        # target 1 ... monster in your GY; Special Summon that target..." --
        # both halves there are already on the effect side of their colon.)
        sentence = raw_sentence.rsplit(":", 1)[-1]
        restriction = _extract_restriction(sentence)

        matched_gy_output = False
        for tag, patterns, carries_restriction in _OUTPUT_REQUIREMENTS:
            if all(p.search(sentence) for p in patterns):
                outputs.add(Signal(tag, restriction if carries_restriction else None))
                if carries_restriction and tag in _IMPLIES_WANTS_GY_FODDER:
                    matched_gy_output = True

        for tag, patterns, carries_restriction in _INPUT_REQUIREMENTS:
            if all(p.search(sentence) for p in patterns):
                inputs.add(Signal(tag, restriction if carries_restriction else None))

        if matched_gy_output:
            inputs.add(Signal(t.WANTS_GY_FODDER, restriction))

    return Tags(outputs=frozenset(outputs), inputs=frozenset(inputs))
