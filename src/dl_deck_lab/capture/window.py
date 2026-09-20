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


def list_window_titles() -> list[str]:
    """All currently open window titles, for figuring out what to pass to
    ``--window-title`` when the default guess doesn't match (see `dl-capture
    --list-windows`). Excludes windows with a blank title -- there are
    usually many of those (background/helper processes) and they're never
    what you want here.
    """
    return [w.title for w in pygetwindow.getAllWindows() if w.title.strip()]


def find_window(title_substring: str = "Duel Links") -> WindowRegion:
    """Finds the first open window whose title contains ``title_substring``.

    Raises ``LookupError`` if no matching window is found, e.g. the game
    isn't running, is running under a different window title than expected,
    or is in a fullscreen mode pygetwindow can't see. Run
    ``dl-capture --list-windows`` to see every open window's actual title.
    """
    matches = [
        w for w in pygetwindow.getAllWindows() if title_substring.lower() in w.title.lower()
    ]
    if not matches:
        raise LookupError(
            f"No window found with title containing {title_substring!r}. "
            "Run `dl-capture --list-windows` to see actual open window titles, "
            "then pass the right one with --window-title. If Duel Links isn't "
            "listed at all, try switching it out of fullscreen/exclusive mode."
        )
    window = matches[0]
    return WindowRegion(left=window.left, top=window.top, width=window.width, height=window.height)
