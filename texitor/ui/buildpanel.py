# build output panel - floating overlay showing compiler output
# opens on :build/:compile, streams lines as they arrive, q/escape to close
from __future__ import annotations

from textual.widget import Widget
from textual.strip import Strip
from rich.text import Text
from rich.style import Style
from rich.console import Console

from texitor.core.theme import theme as _theme

_BG       = _theme.bg_alt
_BG_HEAD  = _theme.bg_alt
_FG       = _theme.fg
_FG_DIM   = _theme.fg_dim
_GREEN    = _theme.green
_RED      = _theme.red
_YELLOW   = _theme.yellow
_ACCENT   = _theme.accent
_BORDER   = _theme.border

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

# box chars
_TL = "╭"; _TR = "╮"; _BL = "╰"; _BR = "╯"; _H = "─"; _V = "│"


def _strip(t, w):
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(w)


class BuildPanel(Widget):
    # floating panel that shows compiler output
    # app controls display: block/none
    # _lines is list of (text, is_stderr)

    DEFAULT_CSS = ""  # handled by app CSS

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._lines = []
        self._scroll = 0
        self._status = "idle"   # idle | running | success | error
        self._engine = ""
        self._file = ""

    def reset(self, engine, filePath):
        self._lines = []
        self._scroll = 0
        self._status = "running"
        self._engine = engine
        self._file = filePath
        self.refresh()

    def appendLine(self, text, isErr=False):
        self._lines.append((text, isErr))
        self._scroll = max(0, len(self._lines) - self._innerHeight())
        self.refresh()

    def setDone(self, returncode):
        self._status = "success" if returncode == 0 else "error"
        self.refresh()

    def scrollUp(self, n=3):
        self._scroll = max(0, self._scroll - n)
        self.refresh()

    def scrollDown(self, n=3):
        maxScroll = max(0, len(self._lines) - self._innerHeight())
        self._scroll = min(maxScroll, self._scroll + n)
        self.refresh()

    def _innerHeight(self):
        return max(1, self.size.height - 2)  # minus header + footer

    def get_content_height(self, container, viewport, width):
        return 30

    def render_line(self, y):
        w = self.size.width
        if w == 0:
            return Strip([])

        if y == 0:
            return self._renderHeader(w)

        if y == self.size.height - 1:
            return self._renderFooter(w)

        lineIdx = y - 1 + self._scroll
        if lineIdx < len(self._lines):
            return self._renderOutputLine(self._lines[lineIdx], w)

        # empty filler row
        t = Text(no_wrap=True)
        t.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        t.append(" " * max(0, w - 2), style=Style(bgcolor=_BG))
        t.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        return _strip(t, w)

