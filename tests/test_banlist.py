import json

from dl_deck_lab.decks.banlist import load_banlist_limits

NAMES_BY_ID = {
    "id-1": "Pot of Greed",
    "id-2": "Raigeki",
}


def test_resolves_known_card_names_to_ids(tmp_path):
    path = tmp_path / "banlist.json"
    path.write_text(json.dumps({"Pot of Greed": "forbidden", "Raigeki": "limit1"}))

    limits = load_banlist_limits(str(path), NAMES_BY_ID)

    assert limits == {"id-1": 0, "id-2": 1}


def test_unknown_card_name_is_skipped_not_fatal(tmp_path, capsys):
    path = tmp_path / "banlist.json"
    path.write_text(json.dumps({"Totally Not A Real Card": "forbidden", "Pot of Greed": "limit2"}))

    limits = load_banlist_limits(str(path), NAMES_BY_ID)

    assert limits == {"id-1": 2}
    assert "Totally Not A Real Card" in capsys.readouterr().err


def test_unknown_legality_value_is_skipped_not_fatal(tmp_path, capsys):
    path = tmp_path / "banlist.json"
    path.write_text(json.dumps({"Pot of Greed": "banned-forever"}))

    limits = load_banlist_limits(str(path), NAMES_BY_ID)

    assert limits == {}
    assert "banned-forever" in capsys.readouterr().err
