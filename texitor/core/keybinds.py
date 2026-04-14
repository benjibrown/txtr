# keybind registry
from __future__ import annotations
import tomllib
from pathlib import Path
from texitor.core.modes import Mode

# default keybinds, overridden by user config if present
# writing all these took way too long but should be a good starting point. mostly just nabbed from vim/nvim because who uses nano 
_DEFAULTS = {
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
        "/":       "enter_search",
        "?":       "open_help",
        "n":       "search_next",
        "N":       "search_prev",
        # edit
        "d d":     "delete_line",
        "_ d d":   "blackhole_delete_line",
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
    Mode.INSERT: {
        "escape":    "enter_normal",
        "ctrl+[":    "enter_normal",
        "backspace": "backspace",
        "enter":     "newline",
        "tab":       "insert_tab",
        "shift+tab": "clear_tab_stops",
        "ctrl+w":    "delete_word_before",
        "ctrl+u":    "delete_to_line_start",
        "ctrl+space":"accept_autocomplete",
        "up":        "cursor_up",
        "down":      "cursor_down",
        "left":      "cursor_left",
        "right":     "cursor_right",
    },
    Mode.VISUAL: {
        "escape": "enter_normal",
        ":":      "enter_command",
        "y":      "yank_selection",
        "d":      "delete_selection",
        ">":      "indent",
        "<":      "dedent",
        # motions — all extend the selection
        "h":      "cursor_left",
        "j":      "cursor_down",
        "k":      "cursor_up",
        "l":      "cursor_right",
        "w":      "word_forward",
        "b":      "word_backward",
        "e":      "word_end",
        "0":      "line_start",
        "$":      "line_end",
        "g g":    "goto_first_line",
        "G":      "goto_last_line",
        "ctrl+d": "scroll_half_down",
        "ctrl+u": "scroll_half_up",
        "up":     "cursor_up",
        "down":   "cursor_down",
        "left":   "cursor_left",
        "right":  "cursor_right",
    },
    Mode.VISUAL_LINE: {
        "escape": "enter_normal",
        ":":      "enter_command",
        "y":      "yank_selection",
        "d":      "delete_selection",
        ">":      "indent",
        "<":      "dedent",
        # motions — all extend the selection
        "h":      "cursor_left",
        "j":      "cursor_down",
        "k":      "cursor_up",
        "l":      "cursor_right",
        "w":      "word_forward",
        "b":      "word_backward",
        "e":      "word_end",
        "0":      "line_start",
        "$":      "line_end",
        "g g":    "goto_first_line",
        "G":      "goto_last_line",
        "ctrl+d": "scroll_half_down",
        "ctrl+u": "scroll_half_up",
        "up":     "cursor_up",
        "down":   "cursor_down",
        "left":   "cursor_left",
        "right":  "cursor_right",
    },
    Mode.COMMAND: {
        "escape": "enter_normal",
        "enter":  "execute_command",
    },
    Mode.SEARCH: {
        "escape": "enter_normal",
        "enter":  "execute_search",
    },
}
# TODO - add the rest later


# registry for keybinds, with defaults and user overrides
class KeybindRegistry:
    def __init__(self):
        # prevent mutation
        self._map = {
            mode: dict(binds) for mode, binds in _DEFAULTS.items()
        }

    def load_toml(self, path):
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

    def get(self, mode, key):
        return self._map.get(mode, {}).get(key)

    def all_for_mode(self, mode):
        return dict(self._map.get(mode, {}))
