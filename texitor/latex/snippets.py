# snippet manager - loads from toml, matches triggers, expands into buffer

import tomllib
from pathlib import Path

# default snippets bundled with txtr (fallback if no user config)
defaultPath = Path(__file__).parent / "snippets.toml"
userPath = Path.home() / ".config" / "txtr" / "snippets.toml"


class SnippetManager:
    def __init__(self):
        # flat trigger map: trigger_str -> {name, body}
        self._triggers = {}

    def load(self, path=None):
        # user config takes priority, falls back to bundled defaults
        target = Path(path) if path else (userPath if userPath.exists() else defaultPath)
        if not target.exists():
            return
        with open(target, "rb") as f:
            data = tomllib.load(f)

        self._triggers = {}
        # flatten all sections into one lookup
        for section in data.values():
            if not isinstance(section, dict):
                continue
            for snippet in section.values():
                if isinstance(snippet, dict) and "trigger" in snippet:
                    self._triggers[snippet["trigger"]] = snippet

    def findTrigger(self, textBefore):
        # returns (trigger, snippet) if end of textBefore matches a known trigger
        for trigger, snippet in self._triggers.items():
            if textBefore.endswith(trigger):
                return trigger, snippet
        return None, None

    def allSnippets(self):
        return dict(self._triggers)
