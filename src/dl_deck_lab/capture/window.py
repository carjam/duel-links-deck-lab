"""Locates the Duel Links game window on Windows so we capture just that region.

Windows-only: relies on ``pygetwindow``, which wraps the Win32 window APIs.
Not importable on Linux/macOS/WSL -- that's intentional, see docs/ARCHITECTURE.md.
"""

from __future__ import annotations

import dataclasses

import pygetwindow


@dataclasses.dataclass(frozen=True)
class WindowRegion:
    left: int
    top: int
    width: int
    height: int


def find_window(title_substring: str = "Duel Links") -> WindowRegion:
    """Finds the first open window whose title contains ``title_substring``.

    Raises ``LookupError`` if no matching window is found, e.g. the game
    isn't running or is running under a different window title than expected
    (pass a different ``--window-title`` in that case).
    """
    matches = [
        w for w in pygetwindow.getAllWindows() if title_substring.lower() in w.title.lower()
    ]
    if not matches:
        raise LookupError(
            f"No window found with title containing {title_substring!r}. "
            "Is Duel Links running? Pass --window-title to match a different title."
        )
    window = matches[0]
    return WindowRegion(left=window.left, top=window.top, width=window.width, height=window.height)
