# info panel overlay - neutral floating popup for plugin/info style views
# no build-specific status chrome

from __future__ import annotations

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.theme import theme as _theme

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

_BG = _theme.bg
_BG_ALT = _theme.bg_alt
_FG = _theme.fg
_FG_DIM = _theme.fg_dim
_FG_KEY = _theme.accent
_FG_SECTION = _theme.accent2
_BORDER = _theme.border
_TITLE_FG = _theme.accent2

_TL = "╭"; _TR = "╮"; _BL = "╰"; _BR = "╯"; _H = "─"; _V = "│"

_W = 76
_H_SIZE = 24


class InfoPanel(Widget):

    DEFAULT_CSS = """
    InfoPanel {
        layer: overlay;
        display: none;
        width: 76;
        height: 24;
    }
    """

    def __init__(self):
        super().__init__()
        self._title = " txtr info "
        self._footer = "  j/k scroll   q close"
        self._rows = []
        self._scrollTop = 0
        self._cursor = -1

    def open(self, title, rows, footer=None):
        self._title = f" {title} "
        self._rows = list(rows)
        self._scrollTop = 0
        self._cursor = self._firstSelectable()
        if footer:
            self._footer = footer
        elif self._cursor >= 0:
            self._footer = "  j/k move   enter open   q close"
        else:
            self._footer = "  j/k scroll   q close"
        self._center()
        self.display = True
        self.refresh()

    def close(self):
        self.display = False

    def scrollDown(self, n=1):
        contentH = _H_SIZE - 4
        maxScroll = max(0, len(self._rows) - contentH)
        self._scrollTop = min(self._scrollTop + n, maxScroll)
        self.refresh()

    def scrollUp(self, n=1):
        self._scrollTop = max(0, self._scrollTop - n)
        self.refresh()

    def hasSelection(self):
        return self._cursor >= 0

    def cursorDown(self):
        if self._cursor < 0:
            self.scrollDown()
            return
        for idx in range(self._cursor + 1, len(self._rows)):
            if self._isSelectable(idx):
                self._cursor = idx
                self._revealCursor()
                self.refresh()
                return


