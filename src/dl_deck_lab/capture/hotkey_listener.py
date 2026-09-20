"""Global hotkey binding for capture-on-keypress (Windows-only, via ``keyboard``).

Deliberately the only form of "automation" this project does: it reacts to a
key the player presses themselves while they manually page through their own
in-game collection screens. It never sends input *into* the game.
"""

from __future__ import annotations

import typing

import keyboard


def wait_for_session(capture_key: str, stop_key: str, on_capture: typing.Callable[[], None]) -> None:
    """Blocks, calling ``on_capture`` each time ``capture_key`` is pressed,
    until ``stop_key`` is pressed.
    """
    keyboard.add_hotkey(capture_key, on_capture)
    keyboard.wait(stop_key)
    keyboard.remove_hotkey(capture_key)
