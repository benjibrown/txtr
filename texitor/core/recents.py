# recent files manager - tracks last N opened files
# stored at ~/.config/txtr/recents.json

import json
from pathlib import Path

_RECENTS_PATH = Path.home() / ".config" / "txtr" / "recents.json"
_MAX = 10


def load():
    try:
        return json.loads(_RECENTS_PATH.read_text())
    except Exception:
        return []


def push(filepath):
    p = str(Path(filepath).expanduser().resolve())
    entries = [e for e in load() if e != p]
    entries.insert(0, p)
    entries = entries[:_MAX]
    _RECENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _RECENTS_PATH.write_text(json.dumps(entries, indent=2))


def display_path(filepath):
    # shorten to ~/... form
    try:
        home = Path.home()
        p = Path(filepath)
        return "~/" + str(p.relative_to(home))
    except ValueError:
        return filepath
