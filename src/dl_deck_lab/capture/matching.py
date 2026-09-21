"""Pure title-matching logic, deliberately with zero external dependencies.

Split out of ``window.py`` so this logic is unit-testable on any platform
without installing ``pygetwindow`` (Windows-only) -- the actual OS window
enumeration lives in ``window.py``; this module only knows about strings.
"""

from __future__ import annotations


def is_blank_title(title: str) -> bool:
    """True for a blank/whitespace-only title -- background and helper
    processes usually have several of these, and they're never what
    ``--window-title`` is looking for."""
    return not title.strip()


def title_matches(title: str, substring: str) -> bool:
    """Case-insensitive substring match, e.g. for ``--window-title``."""
    return substring.lower() in title.lower()
