# info panel overlay - neutral floating popup for plugin/info style views
# supports wrapped rows, selectable entries, and streaming text logs

from __future__ import annotations

import textwrap

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
_ROW_KEY_WIDTH = 16


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
        self._sourceRows = []
        self._rows = []
        self._scrollTop = 0
        self._cursor = -1

    def open(self, title, rows, footer=None):
        self._title = f" {title} "
        self._sourceRows = list(rows)
        self._scrollTop = 0
        self._setFooter(footer)
        self._rebuildRows()
        self._center()
        self.display = True
        self.refresh()

    def close(self):
        self.display = False

    def setRows(self, rows, footer=None):
        self._sourceRows = list(rows)
        self._setFooter(footer)
        self._rebuildRows()
        self.refresh()

    def appendRow(self, row, autoScroll=True):
        self._sourceRows.append(row)
        self._rebuildRows(preserve_cursor=True)
        if autoScroll:
            self._scrollToBottom()
        self.refresh()

    def appendText(self, text, autoScroll=True):
        self.appendRow(("text", text), autoScroll=autoScroll)

    def setFooter(self, footer):
        self._setFooter(footer)
        self.refresh()

    def setTitle(self, title):
        self._title = f" {title} "
        self.refresh()

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

    def on_mouse_scroll_down(self, event):
        self.scrollDown(3)

    def on_mouse_scroll_up(self, event):
        self.scrollUp(3)

    def _setFooter(self, footer):
        if footer:
            self._footer = footer
            return
        self._footer = "  j/k scroll   q close"

    def _center(self):
        screenW = self.app.size.width
        screenH = self.app.size.height
        x = max(0, (screenW - _W) // 2)
        y = max(0, (screenH - _H_SIZE) // 2)
        self.styles.offset = (x, y)

    def _rebuildRows(self, preserve_cursor=False):
        selected_action = self.activate() if preserve_cursor else None
        self._rows = _expandRows(self._sourceRows)

        if selected_action:
            self._cursor = -1
            for idx, row in enumerate(self._rows):
                if len(row) >= 4 and row[3] == selected_action:
                    self._cursor = idx
                    break
        else:
            self._cursor = self._firstSelectable()

        if self._cursor >= 0 and "enter open" not in self._footer and "enter select" not in self._footer:
            self._footer = "  j/k move   enter open   q close"

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

    def _scrollToBottom(self):
        contentH = _H_SIZE - 4
        self._scrollTop = max(0, len(self._rows) - contentH)

    def on_resize(self, event):
        if self.display:
            self._rebuildRows(preserve_cursor=True)
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
            continuation=(kind == "cont"),
        )


def _wrapText(text, width):
    if width <= 0:
        return [text]
    if text == "":
        return [""]
    lines = []
    for raw in str(text).splitlines() or [""]:
        wrapped = textwrap.wrap()
            raw,
            width=width,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=True,
            break_on_hyphens=False,
        )
        lines.extend(wrapped or [""])
    return lines or [""]



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


def _renderHeader(label, width, inner):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_V, style=bs)
    content = f"  {label}"
    t.append(content, style=Style(color=_FG_SECTION, bgcolor=_BG, bold=True))
    t.append(" " * max(0, inner - len(content)), style=Style(bgcolor=_BG))
    t.append(_V, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderText(text, rowIdx, width, inner):
    bg = _BG_ALT if rowIdx % 2 == 0 else _BG
    bs = Style(color=_BORDER, bgcolor=bg)
    t = Text(no_wrap=True)
    t.append(_V, style=bs)
    t.append("  ", style=Style(bgcolor=bg))
    t.append(text[: max(0, inner - 2)], style=Style(color=_FG, bgcolor=bg))
    t.append(" " * inner, style=Style(bgcolor=bg))
    t.append(_V, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderRow(key, val, rowIdx, width, inner, selected=False, selectable=False, continuation=False):
    bg = _theme.bg_popup if selected else (_BG_ALT if rowIdx % 2 == 0 else _BG)
    bs = Style(color=_BORDER, bgcolor=bg)
    t = Text(no_wrap=True)
    t.append(_V, style=bs)
    prefix = "❯ " if selected els"  "
    t.append(prefix, style=Style(color=_FG_KEY, bgcolor=bg, bold=selected))
    keyCol = f"{key:<{_ROW_KEY_WIDTH}}" if not continuation else " " * _ROW_KEY_WIDTH
    t.append("  ", style=Style(bgcolor=bg))
    available = max(0, inner - len(keyCol) - len(prefix) - 4)
    t.append(val[:available], style=Style(color=_FG, bgcolor=bg, bold=selected))
    t.append(" " * inner, style=Style(bgcolor=bg))
    t.append(_V, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)
