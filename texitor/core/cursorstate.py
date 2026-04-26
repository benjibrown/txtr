import json
import os
import time
from pathlib import Path

_MAX_ENTRIES = 1000

# all this does is makes sure ur cursor is placed where u left it when u closed txtr :), should be relatively optimised

def _statePath():
    # xdg if present, otherwise the classic ~/.local/share move
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        root = Path(base).expanduser()
    else:
        root = Path.home() / ".local" / "share"
    return root / "txtr" / "cursor_state.json"


class CursorStateStore:

    def __init__(self, path=None):
        self._path = Path(path) if path else _statePath()
        self._data = None

    def _read(self):
        if self._data is not None:
            return self._data
        if not self._path.exists():
            self._data = {"files": {}}
            return self._data
        try:
            with open(self._path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, json.JSONDecodeError):
            self._data = {"files": {}}
            return self._data

        files = raw.get("files", {}) if isinstance(raw, dict) else {}
        if not isinstance(files, dict):
            files = {}
        self._data = {"files": files}
        return self._data

    def _write(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, sort_keys=True)

    def _prune(self, max_age_days):
        files = self._read()["files"]

