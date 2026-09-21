from dl_deck_lab.synergy.tagging import Signal, extract_tags
from dl_deck_lab.synergy.tags import (
    BANISHES_FROM_GY,
    DESTROYS_SPELL_TRAP,
    DISCARDS_FROM_HAND,
    DRAWS_OR_DIGS,
    EQUIPS_FROM_GY,
    GY_COUNT_RELIANT,
    MILLS_FROM_DECK,
    NEGATES,
    RETURNS_TO_HAND,
    SEARCHES_DECK,
    SPECIAL_SUMMONS_FROM_GY,
    WANTS_GY_FODDER,
)


def _tags_only(signals):
    return {s.tag for s in signals}


# Real effect text pulled from the card database this session, spanning
# different mechanics -- see docs/ROADMAP.md's synergy section for why this
# grounding matters (official text is templated enough for regex to work).


def test_stratos_destroys_and_searches_no_gy():
    text = (
        'When this card is Normal or Special Summoned: You can activate 1 of these effects; '
        '● Destroy Spells/Traps on the field, up to the number of "HERO" monsters you control, '
        'except this card. ● Add 1 "HERO" monster from your Deck to your hand.'
    )
    tags = extract_tags(text)
    assert _tags_only(tags.outputs) == {DESTROYS_SPELL_TRAP, SEARCHES_DECK}
    assert tags.inputs == frozenset()


def test_woodsman_searches_deck():
    text = 'Once per turn, during your Standby Phase: You can add 1 "Polymerization" from your Deck or Graveyard to your hand.'
    tags = extract_tags(text)
    assert SEARCHES_DECK in _tags_only(tags.outputs)


def test_junk_synchron_special_summons_from_gy_with_level_restriction():
    text = (
        "When this card is Normal Summoned: You can target 1 Level 2 or lower monster in your GY; "
        "Special Summon that target in Defense Position, but negate its effects."
    )
    tags = extract_tags(text)
    assert Signal(SPECIAL_SUMMONS_FROM_GY, "level_le_2") in tags.outputs
    assert NEGATES in _tags_only(tags.outputs)
    assert Signal(WANTS_GY_FODDER, "level_le_2") in tags.inputs


def test_miracle_fusion_banishes_from_gy_unrestricted():
    text = 'Fusion Summon 1 "Elemental HERO" Fusion Monster from your Extra Deck, by banishing Fusion Materials mentioned on it from your field or GY.'
    tags = extract_tags(text)
    assert Signal(BANISHES_FROM_GY, None) in tags.outputs


def test_dark_magician_girl_is_gy_count_reliant_with_no_active_effect():
    text = 'Gains 300 ATK for every "Dark Magician" or "Magician of Black Chaos" in the GYs.'
    tags = extract_tags(text)
    assert GY_COUNT_RELIANT in _tags_only(tags.inputs)
    assert tags.outputs == frozenset()


def test_dark_magician_of_chaos_gy_recycle_does_not_false_positive_as_deck_search():
    # Real trap: this card recycles a Spell FROM the GY to hand, not from
    # the Deck -- a naive whole-text search for "add"+"deck"+"hand" would
    # wrongly tag this as searches_deck if it ignored sentence boundaries,
    # since "Deck" and "GY" both appear elsewhere in the full card text.
    text = (
        "During the End Phase, if this card was Normal or Special Summoned this turn: "
        "You can target 1 Spell in your GY; add it to your hand. "
        'You can only use this effect of "Dark Magician of Chaos" once per turn. '
        "If this card destroys an opponent's monster by battle, after damage calculation: "
        "Banish that opponent's monster."
    )
    tags = extract_tags(text)
    assert SEARCHES_DECK not in _tags_only(tags.outputs)
    assert BANISHES_FROM_GY not in _tags_only(tags.outputs)  # banishes the battled monster, not from a GY


def test_monster_reborn_special_summons_from_gy_unrestricted():
    tags = extract_tags("Target 1 monster in either GY; Special Summon it.")
    assert tags.outputs == frozenset({Signal(SPECIAL_SUMMONS_FROM_GY, None)})
    assert tags.inputs == frozenset({Signal(WANTS_GY_FODDER, None)})


def test_card_trader_draws_no_gy_mention():
    text = "Once per turn, during your Standby Phase: You can shuffle 1 card from your hand into the Deck; draw 1 card."
    tags = extract_tags(text)
    assert _tags_only(tags.outputs) == {DRAWS_OR_DIGS}
    assert tags.inputs == frozenset()


def test_cyberdark_edge_equips_from_gy_with_type_restriction():
    text = (
        "If this card is Normal Summoned: Target 1 Level 3 or lower Dragon monster in your GY; "
        "equip that Dragon monster to this card."
    )
    tags = extract_tags(text)
    # Named-archetype/Type restriction wins over Level when both are present
    # (see _extract_restriction's priority order) -- Dragon is more specific.
    assert Signal(EQUIPS_FROM_GY, "dragon") in tags.outputs
    assert Signal(WANTS_GY_FODDER, "dragon") in tags.inputs


def test_foolish_burial_mills_from_deck_unrestricted():
    tags = extract_tags("Send 1 monster from your Deck to the GY.")
    assert tags.outputs == frozenset({Signal(MILLS_FROM_DECK, None)})


def test_red_eyes_insight_mills_with_named_restriction_and_searches():
    text = (
        'Send 1 "Red-Eyes" monster from your hand or Deck to the GY; add 1 "Red-Eyes" Spell/Trap '
        'from your Deck to your hand, except "Red-Eyes Insight". '
        'You can only activate 1 "Red-Eyes Insight" per turn.'
    )
    tags = extract_tags(text)
    assert Signal(MILLS_FROM_DECK, "red-eyes") in tags.outputs
    assert SEARCHES_DECK in _tags_only(tags.outputs)


def test_return_of_the_doomed_discards_and_returns_to_hand():
    text = (
        "Discard 1 Monster Card from your hand to the Graveyard. "
        "Return 1 of your monsters destroyed and sent to your Graveyard as a result of "
        "battle during this turn to your hand at the end of this turn."
    )
    tags = extract_tags(text)
    assert DISCARDS_FROM_HAND in _tags_only(tags.outputs)
    assert RETURNS_TO_HAND in _tags_only(tags.outputs)


def test_mask_change_does_not_false_positive_as_mill_via_extra_deck():
    # Real bug caught against the real collection: "send it to the GY" plus
    # an unrelated "from your Extra Deck" mention in the same sentence
    # false-positived as MILLS_FROM_DECK (bare "deck" doesn't distinguish
    # "Extra Deck" from the Main Deck).
    text = (
        'Target 1 "HERO" monster you control; send it to the GY, also, after that, '
        'if it left the field by this effect, Special Summon 1 "Masked HERO" monster '
        "from your Extra Deck with the same Attribute that the sent monster had when "
        "it was on the field (its original Attribute, if face-down)."
    )
    tags = extract_tags(text)
    assert MILLS_FROM_DECK not in _tags_only(tags.outputs)


def test_masked_hero_dian_condition_clause_gy_does_not_leak_into_effect_clause():
    # Real bug: the GY mention is in the *condition* ("...destroys a monster
    # and sends it to the GY:"), not the effect ("Special Summon ... from
    # your Deck") -- matching the whole sentence wrongly tagged this as
    # special_summons_from_gy. Splitting on the last ':' fixes it.
    text = (
        'Must be Special Summoned with "Mask Change". When this card destroys an '
        "opponent's monster by battle and sends it to the GY: You can Special "
        'Summon 1 Level 4 or lower "HERO" monster from your Deck.'
    )
    tags = extract_tags(text)
    assert SPECIAL_SUMMONS_FROM_GY not in _tags_only(tags.outputs)


def test_no_effect_text_tags_empty():
    assert extract_tags(None).outputs == frozenset()
    assert extract_tags(None).inputs == frozenset()
    assert extract_tags("").outputs == frozenset()
