import uuid

import ygojson.database as ygodb

from dl_deck_lab.carddb.loader import all_named_cards, duel_links_cards


def make_card(name, *, duel_links_rarity=None, illegal=False, has_english=True):
    text = {}
    if has_english:
        text[ygodb.Language.ENGLISH] = ygodb.CardText(name=name)
    return ygodb.Card(
        id=uuid.uuid4(),
        text=text,
        card_type=ygodb.CardType.MONSTER,
        duel_links_rarity=duel_links_rarity,
        illegal=illegal,
    )


def make_db(cards):
    db = ygodb.Database()
    for c in cards:
        db.add_card(c)
    return db


def test_duel_links_cards_filters_to_tagged_and_legal():
    tagged = make_card("Tagged", duel_links_rarity=ygodb.VideoGameRaity.ULTRA)
    untagged = make_card("Untagged", duel_links_rarity=None)
    illegal_but_tagged = make_card(
        "Illegal", duel_links_rarity=ygodb.VideoGameRaity.SUPER, illegal=True
    )
    db = make_db([tagged, untagged, illegal_but_tagged])

    assert duel_links_cards(db) == [tagged]


def test_all_named_cards_ignores_duel_links_tagging_but_requires_english_name():
    tagged = make_card("Tagged", duel_links_rarity=ygodb.VideoGameRaity.ULTRA)
    untagged = make_card("Untagged", duel_links_rarity=None)
    no_english = make_card("No English", has_english=False)
    illegal = make_card("Illegal", illegal=True)
    db = make_db([tagged, untagged, no_english, illegal])

    result = all_named_cards(db)

    assert {c.text[ygodb.Language.ENGLISH].name for c in result} == {"Tagged", "Untagged"}
