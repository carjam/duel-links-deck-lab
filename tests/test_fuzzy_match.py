from dl_deck_lab.ocr.fuzzy_match import match_card_name

KNOWN_NAMES = {
    "c1": "Blue-Eyes White Dragon",
    "c2": "Dark Magician",
    "c3": "Pot of Greed",
}


def test_exact_match():
    result = match_card_name("Pot of Greed", KNOWN_NAMES)
    assert result.card_id == "c3"
    assert result.confident


def test_ocr_typo_still_matches():
    # 'l' misread as '1', common OCR confusion.
    result = match_card_name("B1ue-Eyes White Dragon", KNOWN_NAMES)
    assert result.card_id == "c1"
    assert result.confident


def test_garbage_input_is_not_confident():
    result = match_card_name("###unreadable###", KNOWN_NAMES)
    assert not result.confident
    assert result.card_id is None
