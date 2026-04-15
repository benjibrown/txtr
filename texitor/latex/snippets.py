# snippet manager - loads from toml, matches triggers, expands into buffer
import re
import tomllib
from pathlib import Path

# default snippets bundled with txtr (fallback if no user config)
defaultPath = Path(__file__).parent / "snippets.toml"
userPath = Path.home() / ".config" / "txtr" / "snippets.toml"

# TODO - new tab stop system, dont use | --> better syntax should be ${1} ${2}, ${1:placeholder}
# TODO - keep support for | just in case 
_STOP_RE = re.compile(r"\$\{(\d+)(?::([^}]*))?\}") # i hope this works

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
        # returns list of (row, col) tab stop positions - sort by stop number 
        # ${N}, ${N:placeholder} and | 
        trigLen = len(trigger)
        curRow = buf.cursor_row
        curCol = buf.cursor_col

        # remove the trigger text before cursor
        line = buf.lines[curRow]
        buf.lines[curRow] = line[:curCol - trigLen] + line[curCol:]
        buf.cursor_col = curCol - trigLen

        # pass 1 - find all numbered stops 
        numStops = {}
        for m in _STOP_RE.finditer(body):
            n = int(m.group(1))
            if n not in numStops:
                numStops[n] = m.group(2) or ""

        pipeCount = body.count("|")
        nextN = (max(numStops.keys()) +1) if numStops else 1
        pipeNums = list(range(nextN, nextN + pipeCount))

        # pass 2  - build clean text 
        # walk body to find tab stop positions and build clean text
        cleanBody = ""
        stopPos = {} # probably row, col, len 
        pipeIdx = 0 
        row = buf.cursor_row
        col = buf.cursor_col
        i = 0
        while i < len(body):
            m = _STOP_RE.match(body, i)
            if m:
                n = int(m.group(1))
                ph = m.group(2) or ""
                # first occurence of each num records the position (hopefully)
                if n not in stopPos:
                    stopPos[n] = (row, col, len(ph))
                cleanBody += ph 
                col += len(ph)
                i = m.end()
                continue
               
            ch = body[i]

            if ch == "|": # legacy 
                if pipeIdx < len(pipeNums):
                    n = pipeNums[pipeIdx]
                    stopPos[n] = (row, col, 0)
                    pipeIdx += 1
                i += 1
                continue
            if ch == "\n":
                cleanBody += ch
                row += 1
                col = 0
            else:
                cleanBody += ch
                col += 1
            i += 1
        buf.insert(cleanBody)
        buf.modified = True
        return [(r,c,l) for _, (r,c,l) in sorted(stopPos.items())]
