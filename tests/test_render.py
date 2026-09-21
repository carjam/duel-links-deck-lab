from dl_deck_lab.decks.render import CardRenderInfo, render_deck_html
from dl_deck_lab.decks.schema import Deck, DeckCard

TINY_URI = "data:image/svg+xml;utf8,<svg/>"


def make_deck():
    return Deck(
        name="Test Deck",
        cards=[
            DeckCard(card_id="trap-1", name="A Trap", zone="main", quantity=2),
            DeckCard(card_id="mon-1", name="A Monster", zone="main", quantity=3),
            DeckCard(card_id="spell-1", name="A Spell", zone="main", quantity=1),
            DeckCard(card_id="extra-1", name="An Extra Deck Card", zone="extra", quantity=2),
        ],
    )


def make_card_info():
    return {
        "trap-1": CardRenderInfo(name="A Trap", card_type="Trap", image_data_uri=TINY_URI),
        "mon-1": CardRenderInfo(name="A Monster", card_type="Monster", image_data_uri=TINY_URI),
        "spell-1": CardRenderInfo(name="A Spell", card_type="Spell", image_data_uri=TINY_URI),
        "extra-1": CardRenderInfo(name="An Extra Deck Card", card_type="Monster", image_data_uri=TINY_URI),
    }


def test_renders_deck_name_and_totals():
    html = render_deck_html(make_deck(), make_card_info())
    assert "<title>Test Deck</title>" in html
    assert "Main Deck 6" in html
    assert "Extra Deck 2" in html


def test_monster_section_comes_before_spell_and_trap():
    html = render_deck_html(make_deck(), make_card_info())
    monster_idx = html.index("Main Deck — Monsters")
    spell_idx = html.index("Main Deck — Spells")
    trap_idx = html.index("Main Deck — Traps")
    assert monster_idx < spell_idx < trap_idx


def test_extra_deck_section_present_and_separate_from_main():
    html = render_deck_html(make_deck(), make_card_info())
    extra_idx = html.index("Extra Deck</h2>")
    trap_idx = html.index("Main Deck — Traps")
    assert trap_idx < extra_idx


def test_copy_count_badges_reflect_quantity():
    html = render_deck_html(make_deck(), make_card_info())
    assert "&times;3" in html  # the monster
    assert "&times;2" in html  # both the trap and the extra deck card


def test_empty_section_is_omitted():
    deck = Deck(name="Monsters Only", cards=[DeckCard(card_id="mon-1", name="A Monster", zone="main", quantity=3)])
    card_info = {"mon-1": CardRenderInfo(name="A Monster", card_type="Monster", image_data_uri=TINY_URI)}

    html = render_deck_html(deck, card_info)

    assert "Main Deck — Spells" not in html
    assert "Main Deck — Traps" not in html
    assert "Extra Deck</h2>" not in html


def test_card_name_is_html_escaped():
    deck = Deck(name="Test", cards=[DeckCard(card_id="m1", name="A & B <script>", zone="main", quantity=1)])
    card_info = {"m1": CardRenderInfo(name="A & B <script>", card_type="Monster", image_data_uri=TINY_URI)}

    html = render_deck_html(deck, card_info)

    assert "<script>" not in html
    assert "A &amp; B &lt;script&gt;" in html
