# config manager - loads/saves ~/.config/txtr/config.toml
# single source of truth for all user preferences
# safe to call get() before load() - returns defaults

import tomllib
import tomli_w
from pathlib import Path
from copy import deepcopy

_userPath = Path.home() / ".config" / "txtr" / "config.toml"
_bundledPath = Path(__file__).parent.parent / "core" / "config_default.toml"

# all defaults live here - if the user config is missing a key, we fall back to these
_DEFAULTS = {
    "editor": {
        "relative_numbers": False,
        "tab_width":        4,
        "auto_pairs":       True,
        "system_clipboard": False,
        "blackhole_delete": False,
        "indent_guides":    True,
        "wrap":             True, # soft line wrap config
    },
    "compiler": {
        "engine":           "latexmk",
        "aux_dir":          ".aux",
        "custom_cmd":       "",
        "autocompile":      "off", # 3 modes - always/off/save - always doesnt require initialising, off will never autocompile and save will autocompile when the file is saved but only if user initialises the compiler once first
        "build_log_autohide":   False,
        "build_log_autoclose":  False,
    },
    "theme": {
        "name":        "catppuccin",
        "custom_path": "",
    },
    "statusbar": {
        "show_wordcount": False, # not implemented yet - might do as demo plugin so this might get removed to be put under plugin config
        "show_col":       True,
        "show_mode":      True,
    },
}


class ConfigManager:
    # on init, load defs 
    def __init__(self):
        self._data = deepcopy(_DEFAULTS)

    def load(self, path=None):
        # load from user config, fall back to bundled defaults for missing keys
        target = Path(path) if path else _userPath
        if not target.exists():
            return
        with open(target, "rb") as f:
            raw = tomllib.load(f)
        # deep merge - user values override defaults, missing keys stay as defaults
        for section, values in raw.items():
            if section not in self._data:
                self._data[section] = {}
            if isinstance(values, dict):
                self._data[section].update(values)
            else:
                self._data[section] = values

    def get(self, section, key, default=None):
        # get a config value - returns default if section/key missing
        return self._data.get(section, {}).get(key, default)

    def set(self, section, key, value):
        # set a value and immediately persist to disk
        if section not in self._data:
            self._data[section] = {}
        self._data[section][key] = value
        self._save()

    def getSection(self, section):
        # get all keys in a section as a dict
        return dict(self._data.get(section, {}))

    def all(self):
        # get the full config dict (read only - don't mutate directly)
        return deepcopy(self._data)

    def _save(self):
        _userPath.parent.mkdir(parents=True, exist_ok=True)
        with open(_userPath, "wb") as f:
            tomli_w.dump(self._data, f)


# peak config system
config = ConfigManager()

