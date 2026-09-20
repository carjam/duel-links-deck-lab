"""Grabs a screenshot of a specific screen region (Windows-only, via mss)."""

from __future__ import annotations

import mss
import mss.tools

from dl_deck_lab.capture.window import WindowRegion


def capture_region(region: WindowRegion, out_path: str) -> None:
    bbox = {
        "left": region.left,
        "top": region.top,
        "width": region.width,
        "height": region.height,
    }
    with mss.mss() as sct:
        shot = sct.grab(bbox)
        mss.tools.to_png(shot.rgb, shot.size, output=out_path)
