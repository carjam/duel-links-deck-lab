from dl_deck_lab.capture.matching import is_blank_title, title_matches


def test_is_blank_title():
    assert is_blank_title("") is True
    assert is_blank_title("   ") is True
    assert is_blank_title("Yu-Gi-Oh! DUEL LINKS") is False


def test_title_matches_is_case_insensitive():
    assert title_matches("Yu-Gi-Oh! DUEL LINKS", "duel links") is True
    assert title_matches("Yu-Gi-Oh! DUEL LINKS", "Duel Links") is True


def test_title_matches_is_a_substring_match():
    assert title_matches("Yu-Gi-Oh! DUEL LINKS", "Yu-Gi-Oh") is True
    assert title_matches("Yu-Gi-Oh! DUEL LINKS", "Master Duel") is False


def test_title_matches_empty_substring_matches_anything():
    assert title_matches("Anything at all", "") is True
