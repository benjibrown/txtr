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

    def cursorUp(self):
        if self._cursor < 0:
            self.scrollUp()
            return
        for idx in range(self._cursor - 1, -1, -1):
            if self._isSelectable(idx):
                self._cursor = idx
                self._revealCursor()
                self.refresh()
                return

    def activate(self):
        if self._cursor < 0 or self._cursor >= len(self._rows):
            return None
        row = self._rows[self._cursor]
        if len(row) >= 4:
            return row[3]
        return None

    def _firstSelectable(self):
        for idx in range(len(self._rows)):
            if self._isSelectable(idx):
                return idx
        return -1

    def _isSelectable(self, idx):
        row = self._rows[idx]
        return row[0] == "row" and len(row) >= 4 and row[3] is not None

    def _revealCursor(self):
        contentH = _H_SIZE - 4
        if self._cursor < self._scrollTop:
            self._scrollTop = self._cursor
        elif self._cursor >= self._scrollTop + contentH:
            self._scrollTop = self._cursor - contentH + 1

    def on_mouse_scroll_down(self, event):
        self.scrollDown(3)

    def on_mouse_scroll_up(self, event):
        self.scrollUp(3)

    def _center(self):
        screenW = self.app.size.width
        screenH = self.app.size.height
        x = max(0, (screenW - _W) // 2)
        y = max(0, (screenH - _H_SIZE) // 2)
        self.styles.offset = (x, y)

    def on_resize(self, event):
        if self.display:
            self._center()

    def get_content_height(self, container, viewport, width):
        return _H_SIZE

    def render_line(self, y):
        width = self.size.width
        inner = width - 2

        if y == 0:
            return _renderTopBorder(width, inner, self._title)
        if y == _H_SIZE - 2:
            return _renderDivider(width, inner)
        if y == _H_SIZE - 1:
            return _renderFooter(width, inner, self._footer)
        if y == _H_SIZE:
            return _renderBottomBorder(width, inner)

        contentY = y - 1
        rowIdx = self._scrollTop + contentY
        if rowIdx >= len(self._rows):
            return _renderBlank(width, inner)
        kind = self._rows[rowIdx][0]
        if kind == "header":
            return _renderHeader(self._rows[rowIdx][1], width, inner)
        if kind == "text":
            return _renderText(self._rows[rowIdx][1], rowIdx, width, inner)
        if kind == "gap":
            return _renderBlank(width, inner)
        return _renderRow(
            self._rows[rowIdx][1],
            self._rows[rowIdx][2],
            rowIdx,
            width,
            inner,
            selected=(rowIdx == self._cursor),
            selectable=self._isSelectable(rowIdx),
        )


def _renderTopBorder(width, inner, title):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_TL, style=bs)
    t.append(_H, style=bs)
    t.append(title, style=Style(color=_TITLE_FG, bgcolor=_BG, bold=True))
    t.append(_H * max(0, inner - 1 - len(title)), style=bs)
    t.append(_TR, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderDivider(width, inner):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append("├", style=bs)
    t.append(_H * inner, style=bs)
    t.append("┤", style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderFooter(width, inner, footer):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_V, style=bs)
    t.append(footer[:inner], style=Style(color=_FG_DIM, bgcolor=_BG))
    t.append(" " * max(0, inner - len(footer)), style=Style(bgcolor=_BG))
    t.append(_V, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderBottomBorder(width, inner):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_BL, style=bs)
    t.append(_H * inner, style=bs)
    t.append(_BR, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderBlank(width, inner):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_V, style=bs)
    t.append(" " * inner, style=Style(bgcolor=_BG))
    t.append(_V, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


