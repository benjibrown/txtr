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
        now = time.time()
        max_age_days = max(1, int(max_age_days or 30))
        cutoff = now - (max_age_days * 86400)
        changed = False

        stale = [
            path for path, state in files.items()
            if not isinstance(state, dict) or float(state.get("ts", 0)) < cutoff
        ]
        for path in stale:
            files.pop(path, None)
            changed = True

        if len(files) <= _MAX_ENTRIES:
            return changed

        # tiny cap so this file never turns into a landfill
        ranked = sorted(
            files.items(),
            key=lambda item: float(item[1].get("ts", 0)) if isinstance(item[1], dict) else 0,
            reverse=True,
        )
        keep = dict(ranked[:_MAX_ENTRIES])
        files.clear()
        files.update(keep)
        return True

    def get(self, path, max_age_days=30):
        if self._prune(max_age_days):
            self._write()
        state = self._read()["files"].get(str(path))
        if not isinstance(state, dict):
            return None
        return {
            "row": max(0, int(state.get("row", 0))),
            "col": max(0, int(state.get("col", 0))),
            "scroll_top": max(0, int(state.get("scroll_top", 0))),
        }

    def update(self, path, row, col, scroll_top=0, max_age_days=30):
        data = self._read()
        data["files"][str(path)] = {
            "row": max(0, int(row)),
            "col": max(0, int(col)),
            "scroll_top": max(0, int(scroll_top)),
            "ts": time.time(),
        }
        self._prune(max_age_days)
        self._write()


store = CursorStateStore() # i love instantiation
