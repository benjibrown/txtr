# keybind registry
from __future__ import annotations
import tomllib
from pathlib import Path
from texitor.core.modes import Mode

# default keybinds, overridden by user config if present
# writing all these took way too long but should be a good starting point. mostly just nabbed from vim/nvim because who uses nano 
_DEFAULTS: dict[Mode, dict[str, str]] = {
    Mode.NORMAL: {
        # nav
        "h":       "cursor_left",
        "j":       "cursor_down",
        "k":       "cursor_up",
        "l":       "cursor_right",
        "w":       "word_forward",
        "b":       "word_backward",
        "e":       "word_end",
        "0":       "line_start",
        "$":       "line_end",
        "g g":     "goto_first_line",
        "G":       "goto_last_line",
        "ctrl+d":  "scroll_half_down",
        "ctrl+u":  "scroll_half_up",
        # arrow keys (for mouse-free nav)
        "up":      "cursor_up",
        "down":    "cursor_down",
        "left":    "cursor_left",
        "right":   "cursor_right",
        # modes
        "i":       "enter_insert",
        "I":       "enter_insert_bol",
        "a":       "enter_insert_after",
        "A":       "enter_insert_eol",
        "o":       "open_line_below",
        "O":       "open_line_above",
        "v":       "enter_visual",
        "V":       "enter_visual_line",
        ":":       "enter_command",
        # edit
        "d d":     "delete_line",
        "y y":     "yank_line",
        "p":       "paste_after",
        "P":       "paste_before",
        "u":       "undo",
        "ctrl+r":  "redo",
        "x":       "delete_char",
        "r":       "replace_char",
        ">":       "indent",
        "<":       "dedent",
    },
}
# TODO - add the rest later


# registry for keybinds, with defaults and user overrides
class KeybindRegistry:
    def __init__(self):
        # prevent mutation
        self._map: dict[Mode, dict[str, str]] = {
            mode: dict(binds) for mode, binds in _DEFAULTS.items()
        }

    def load_toml(self, path: Path):
        # keyboards.toml as per
        with open(path, "rb") as fh:
            data = tomllib.load(fh)

        section_to_mode = {
            "normal":       Mode.NORMAL, # yes i really pressed tab twice so it lines up 
            "insert":       Mode.INSERT,
            "visual":       Mode.VISUAL,
            "visual_line":  Mode.VISUAL_LINE,
            "command":      Mode.COMMAND,
        }
        for section, mode in section_to_mode.items():
            overrides = data.get(section, {})
            self._map.setdefault(mode, {}).update(overrides)

    def get(self, mode: Mode, key: str):
        return self._map.get(mode, {}).get(key)

    def all_for_mode(self, mode: Mode):
        return dict(self._map.get(mode, {}))
