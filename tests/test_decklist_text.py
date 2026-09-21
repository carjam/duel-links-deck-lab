from dl_deck_lab.decks.decklist_text import parse_decklist_text


def test_parses_quantity_and_name():
    text = """
    # Main Deck
    3 Elemental HERO Stratos
    1 Fusion Gate

    # Extra Deck
    2 Masked HERO Anki
    """
    lines = parse_decklist_text(text)

    assert [(l.quantity, l.name, l.zone) for l in lines] == [
        (3, "Elemental HERO Stratos", "main"),
        (1, "Fusion Gate", "main"),
        (2, "Masked HERO Anki", "extra"),
    ]


def test_defaults_quantity_to_one_and_zone_to_main():
    lines = parse_decklist_text("Pot of Greed")
    assert lines == [type(lines[0])(quantity=1, name="Pot of Greed", zone="main")]


def test_blank_lines_and_plain_comments_are_ignored():
    text = """
    # just a note, no zone keyword here
    3 Dark Magician

    """
    lines = parse_decklist_text(text)
    assert len(lines) == 1
    assert lines[0].name == "Dark Magician"
    assert lines[0].zone == "main"


def test_card_name_that_starts_with_a_digit_is_not_mistaken_for_a_header():
    lines = parse_decklist_text("2 7 Colored Fish")
    assert lines == [type(lines[0])(quantity=2, name="7 Colored Fish", zone="main")]
