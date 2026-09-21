import uuid

import ygojson.database as ygodb

from dl_deck_lab.recommender.archetypes import build_archetype_index


def make_card_simple():
    return ygodb.Card(id=uuid.uuid4(), text={}, card_type=ygodb.CardType.MONSTER)


def make_series(name, members, *, archetype=True, english=True):
    return ygodb.Series(
        id=uuid.uuid4(),
        name={ygodb.Language.ENGLISH: name} if english else {},
        archetype=archetype,
        members=set(members),
    )


def make_db(series_list):
    db = ygodb.Database()
    for s in series_list:
        db.add_series(s)
    return db


def test_only_counts_members_that_are_duel_links_obtainable():
    dl_cards = [make_card_simple() for _ in range(3)]
    non_dl_card = make_card_simple()
    series = make_series("Blue-Eyes", dl_cards + [non_dl_card])
    db = make_db([series])
    dl_ids = {str(c.id) for c in dl_cards}

    [result] = build_archetype_index(db, dl_ids, min_members=3)

    assert result.name == "Blue-Eyes"
    assert len(result.member_card_ids) == 3


def test_series_below_min_members_after_filtering_is_excluded():
    dl_cards = [make_card_simple() for _ in range(2)]
    series = make_series("Tiny Series", dl_cards)
    db = make_db([series])

    result = build_archetype_index(db, {str(c.id) for c in dl_cards}, min_members=3)

    assert result == []


def test_series_without_english_name_is_excluded():
    dl_cards = [make_card_simple() for _ in range(3)]
    series = make_series("No English", dl_cards, english=False)
    db = make_db([series])

    result = build_archetype_index(db, {str(c.id) for c in dl_cards}, min_members=3)

    assert result == []


def test_archetype_flag_is_preserved():
    dl_cards = [make_card_simple() for _ in range(3)]
    series = make_series("A Theme", dl_cards, archetype=False)
    db = make_db([series])

    [result] = build_archetype_index(db, {str(c.id) for c in dl_cards}, min_members=3)

    assert result.is_named_archetype is False
