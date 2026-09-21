from dl_deck_lab.decks.schema import Deck, DeckCard
from dl_deck_lab.decks.validate import validate_deck


def make_card(name, zone, quantity, card_id=None):
    return DeckCard(card_id=card_id or name, name=name, zone=zone, quantity=quantity)


def test_legal_deck_has_no_violations():
    deck = Deck(
        name="Test",
        cards=[make_card(f"Monster {i}", "main", 3) for i in range(8)]
        + [make_card("Extra A", "extra", 2)],
    )
    # 8 unique main-deck cards x 3 = 24, within 20-30.
    assert validate_deck(deck) == []


def test_flags_undersized_main_deck():
    deck = Deck(name="Test", cards=[make_card("Monster A", "main", 3)])
    violations = validate_deck(deck)
    assert any("Main Deck has 3" in v.message for v in violations)


def test_flags_oversized_extra_deck():
    deck = Deck(
        name="Test",
        cards=[make_card(f"Monster {i}", "main", 3) for i in range(7)]
        + [make_card("Extra A", "extra", 3), make_card("Extra B", "extra", 3), make_card("Extra C", "extra", 3)],
    )
    violations = validate_deck(deck)
    assert any("Extra Deck has 9" in v.message for v in violations)


def test_flags_more_than_three_copies():
    deck = Deck(
        name="Test",
        cards=[make_card(f"Monster {i}", "main", 3) for i in range(6)]
        + [make_card("Overplayed", "main", 4, card_id="over-1")],
    )
    violations = validate_deck(deck)
    assert any("Overplayed: 4 copies used" in v.message for v in violations)


def test_flags_using_more_copies_than_owned():
    deck = Deck(
        name="Test",
        cards=[make_card(f"Monster {i}", "main", 3) for i in range(7)]
        + [make_card("Rare Card", "main", 2, card_id="rare-1")],
    )
    violations = validate_deck(deck, owned_copies_by_id={"rare-1": 1})
    assert any("deck uses 2, but collection.json shows only 1 owned" in v.message for v in violations)
