from PIL import Image, ImageDraw

from dl_deck_lab.ocr.layout import Box, GridLayout
from dl_deck_lab.ocr.parser import parse_screenshot


def make_fake_collection_screenshot(path, entries):
    """entries: list of (name, count) per slot, laid out in a 2-col grid."""
    slot_w, slot_h = 300, 100
    cols = 2
    rows = (len(entries) + cols - 1) // cols
    image = Image.new("RGB", (slot_w * cols, slot_h * rows), color="white")
    draw = ImageDraw.Draw(image)

    for i, (name, count) in enumerate(entries):
        row, col = divmod(i, cols)
        x, y = col * slot_w, row * slot_h
        if name is not None:
            draw.text((x + 10, y + 10), name, fill="black")
        if count is not None:
            draw.text((x + 10, y + 50), f"x{count}", fill="black")

    image.save(path)


def test_parse_screenshot_extracts_names_and_counts(tmp_path):
    path = tmp_path / "fake.png"
    make_fake_collection_screenshot(
        str(path),
        [("Dark Magician", 2), ("Pot of Greed", 1), (None, None), (None, None)],
    )

    layout = GridLayout(
        name_box=Box(left=10, top=10, right=290, bottom=40),
        count_box=Box(left=10, top=50, right=100, bottom=90),
        slot_width=300,
        slot_height=100,
        rows=2,
        cols=2,
    )

    readings = parse_screenshot(str(path), layout)

    names = [r.name_text for r in readings]
    assert any("Dark Magician" in n for n in names)
    assert any("Pot of Greed" in n for n in names)

    by_name = {r.name_text: r for r in readings}
    magician = next(r for n, r in by_name.items() if "Dark Magician" in n)
    assert magician.copies_owned == 2
