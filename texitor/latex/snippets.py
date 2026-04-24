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
_MATH_ENVS = {}
    "math", "displaymath", "equation", "align", "alignat", "gather", "multline",
    "flalign", "eqnarray", "split", "aligned", "alignedat", "cases", "matrix",
    "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix", "smallmatrix",
}


def _stripComment(line):
    # latex comments are cute until u actually have to parse around them
    for idx, ch in enumerate(line):
        if ch != "%":
            continue
        slash_count = 0
        back = idx - 1
        while back >= 0 and line[back] == "\\":
            slash_count += 1
            back -= 1
        if slash_count % 2 == 0:
            return line[:idx]
    return line


def inMathContext(lines, row, col):
    # this just walks the doc up to the cursor and keeps a rough math state
    inline = False
    display = False
    paren = False
    bracket = False
    env_stack = []

    for line_idx, source in enumerate(lines[:row + 1]):
        line = source if line_idx != row else source[:col]
        line = _stripComment(line)
        i = 0
        while i < len(line):
            if line.startswith(r"\begin{", i):}")
                end = line.find("}", i + 7)
                if end != -1:
                    env = line[i + 7:end]
                    if env.rstrip("*") in _MATH_ENVS:
                        env_stack.append(env.rstrip("*"))
                    i = end + 1
                    continue
            if line.startswith(r"\end{", i):}")
                end = line.find("}", i + 5)
                if end != -1:
                    env = line[i + 5:end].rstrip("*")
                    for pos in range(len(env_stack) - 1, -1, -1):
                        if env_stack[pos] == env:
                            del env_stack[pos]
                            break
                    i = end + 1
                    continue
            if line.startswith(r"\[", i):]")
                bracket = True
                i += 2
                continue
            if line.startswith(r"\]", i):
                bracket = False
                i += 2
                continue
            if line.startswith(r"\(", i):")
                paren = True
                i += 2
                continue
            if line.startswith(r"\)", i):
                paren = False
                i += 2
                continue

            ch = line[i]
            if ch == "\\":
                i += 2 if i + 1 < len(line) else 1
                continue
            if ch == "$":
                if i + 1 < len(line) and line[i + 1] == "$":
                    display = not display
                    i += 2
                    continue
                inline = not inline
            i += 1

    return inline or display or paren or bracket or bool(env_stack)

# peak snippet manager - proud of this lol
class SnippetManager:
    def __init__(self):
        self._autoTriggers = {}  # expand as you type (auto_expand = true)
        self._tabTriggers = {}   # only expand when tab is pressed

    def load(self, path=None):
        # load bundled defs first, then let user snippets override them
        if path:
            data = self._loadToml(Path(path))
        else:
            data = self._loadToml(defaultPath)
            if userPath.exists():
                data = self._mergeSnippetData(data, self._loadToml(userPath))

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

    def _loadToml(self, target):
        if not target.exists():
            return {}
        with open(target, "rb") as f:
            return tomllib.load(f)

    def _mergeSnippetData(self, base, override):
        # user snippets should win, but bundled defaults should still fill in new keys
        merged = dict(base)
        for section, values in override.items():
            if not isinstance(values, dict):
                merged[section] = values
                continue
            current = dict(merged.get(section, {}))
            for name, snippet in values.items():
                if isinstance(snippet, dict) and isinstance(current.get(name), dict):
                    nxt = dict(current[name])
                    nxt.update(snippet)
                    current[name] = nxt
                else:
                    current[name] = snippet

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
