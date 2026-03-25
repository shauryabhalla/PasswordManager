"""
autotype.py — Simulate keystrokes to type a password into the focused field.

Uses pynput.keyboard.Controller for character-by-character typing.
This avoids clipboard exposure — the password never touches the clipboard.
"""

import time
from pynput.keyboard import Controller, Key

_keyboard = Controller()

# Small delay between keystrokes to ensure reliable input (seconds).
KEYSTROKE_DELAY = 0.012


def type_string(text: str) -> None:
    """
    Type a string character-by-character into the currently focused field.

    A small delay is inserted between keystrokes for reliability with
    slower applications or remote desktop sessions.
    """
    for char in text:
        _keyboard.type(char)
        time.sleep(KEYSTROKE_DELAY)
