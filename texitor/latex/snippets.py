# snippet manager - loads from toml, matches triggers, expands into buffer

import tomllib
from pathlib import Path

# default snippets bundled with txtr (fallback if no user config)
defaultPath = Path(__file__).parent / "snippets.toml"
userPath = Path.home() / ".config" / "txtr" / "snippets.toml"

# peak snippet manager - proud of this lol
class SnippetManager:
    def __init__(self):
        self._autoTriggers = {}  # expand as you type (auto_expand = true)
        self._tabTriggers = {}   # only expand when tab is pressed

    def load(self, path=None):
        # user config takes priority, falls back to bundled defaults
        target = Path(path) if path else (userPath if userPath.exists() else defaultPath)
        if not target.exists():
            return
        with open(target, "rb") as f:
            data = tomllib.load(f)

        self._autoTriggers = {}
        self._tabTriggers = {}
        for section in data.values():
            if not isinstance(section, dict):
                continue
            for snippet in section.values():
                if not isinstance(snippet, dict) or "trigger" not in snippet:
                    continue
                if snippet.get("auto_expand", False):
                    self._autoTriggers[snippet["trigger"]] = snippet
                else:
                    self._tabTriggers[snippet["trigger"]] = snippet

    def findAutoTrigger(self, textBefore):
        # fires as you type - only for auto_expand snippets
        for trigger, snippet in self._autoTriggers.items():
            if textBefore.endswith(trigger):
                return trigger, snippet
        return None, None

    def findTabTrigger(self, textBefore):
        # fires on tab press - for word/env/command snippets
        for trigger, snippet in self._tabTriggers.items():
            if textBefore.endswith(trigger):
                return trigger, snippet
        return None, None

    def allSnippets(self):
        return {**self._autoTriggers, **self._tabTriggers}

    def expandInBuffer(self, trigger, body, buf):
        # deletes trigger from buffer, inserts expanded body
        # returns list of (row, col) tab stop positions
        trigLen = len(trigger)
        curRow = buf.cursor_row
        curCol = buf.cursor_col

        # remove the trigger text before cursor
        line = buf.lines[curRow]
        buf.lines[curRow] = line[:curCol - trigLen] + line[curCol:]
        buf.cursor_col = curCol - trigLen

        # walk body to find tab stop positions and build clean text
        cleanBody = ""
        tabStops = []
        row = buf.cursor_row
        col = buf.cursor_col

        for ch in body:
            if ch == "|":
                tabStops.append((row, col))
            elif ch == "\n":
                cleanBody += ch
                row += 1
                col = 0
            else:
                cleanBody += ch
                col += 1

        buf.insert(cleanBody)
        buf.modified = True
        return tabStops

hel
