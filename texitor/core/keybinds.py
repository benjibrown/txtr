# keybind registry
from __future__ import annotations
import tomllib
from pathlib import Path
from texitor.core.modes import Mode


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
            "normal":      Mode.NORMAL,
            "insert":      Mode.INSERT,
            "visual":      Mode.VISUAL,
            "visual_line": Mode.VISUAL_LINE,
            "command":     Mode.COMMAND,
        }
        for section, mode in section_to_mode.items():
            overrides = data.get(section, {})
            self._map.setdefault(mode, {}).update(overrides)

    def get(self, mode: Mode, key: str):
        return self._map.get(mode, {}).get(key)

    def all_for_mode(self, mode: Mode):
        return dict(self._map.get(mode, {}))
