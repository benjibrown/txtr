# config panel overlay - shows current config as a floating popup
# same border/render pattern as HelpMenu
# open with :config show, close with q/escape

from __future__ import annotations

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

# catppuccin colours - same as helpmenu
# i really shouldnt be hardcoded but i cba to add themes yet lol
_BG         = "#1e1e2e"
_BG_ALT     = "#181825"
_FG_DIM     = "#6c7086"
_FG_KEY     = "#89b4fa"
_FG_VAL     = "#cdd6f4"
_FG_SECTION = "#cba6f7"
_BORDER     = "#45475a"
_TITLE_FG   = "#cba6f7"

_TL = "╭"; _TR = "╮"; _BL = "╰"; _BR = "╯"; _H = "─"; _V = "│"

_W = 60   # popup width
_H_SIZE = 24  # popup height


class ConfigPanel(Widget):

    DEFAULT_CSS = """
    ConfigPanel {
        layer: overlay;
        display: none;
        width: 60;
        height: 24;
    }
    """

    def __init__(self):
        super().__init__()
        self._rows  = []
        self._scrollTop = 0

    def open(self):
        from texitor.core.config import config as cfg
        self._rows = _buildRows(cfg.all())
        self._scrollTop = 0
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

        if y == 0:             return _renderTopBorder(width, inner)
        if y == _H_SIZE - 2:   return _renderDivider(width, inner)
        if y == _H_SIZE - 1:   return _renderFooter(width, inner)
        if y == _H_SIZE:       return _renderBottomBorder(width, inner)

        # content rows between border and footer
        contentY = y - 1
        rowIdx   = self._scrollTop + contentY
        if rowIdx >= len(self._rows):
            return _renderBlank(width, inner)
        kind = self._rows[rowIdx][0]
        if kind == "header":
            return _renderHeader(self._rows[rowIdx][1], width, inner)
        return _renderRow(self._rows[rowIdx][1], self._rows[rowIdx][2], rowIdx, width, inner)


# row builders frfr
def _buildRows(data):
    rows = []
    for section, values in data.items():
        rows.append(("header", f"[{section}]"))
        for k, v in values.items():
            rows.append(("row", k, str(v)))
    return rows


# renderers
def _renderTopBorder(width, inner):

    title = " txtr config "
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
    t.append("├", style=bs); t.append(_H * inner, style=bs); t.append("┤", style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

def _renderFooter(width, inner):
    hints = "  j/k scroll   :config set <section.key> <value>   q close"
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_V, style=bs)

    t.append(hints[:inner], style=Style(color=_FG_DIM, bgcolor=_BG))
    t.append(" " * max(0, inner - len(hints)), style=Style(bgcolor=_BG))
    t.append(_V, style=bs)

    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

def _renderBottomBorder(width, inner):

    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_BL, style=bs); t.append(_H * inner, style=bs); t.append(_BR, style=bs)

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

def _renderRow(key, val, rowIdx, width, inner):
    bg = _BG_ALT if rowIdx % 2 == 0 else _BG
    bs = Style(color=_BORDER, bgcolor=bg)
    t = Text(no_wrap=True)
    t.append(_V, style=bs)
    t.append("  ", style=Style(bgcolor=bg))

    keyCol = f"{key:<22}"
    t.append(keyCol, style=Style(color=_FG_KEY, bgcolor=bg, bold=True))
    t.append("  ", style=Style(bgcolor=bg))
    available = inner - len(keyCol) - 4

    t.append(val[:available], style=Style(color=_FG_VAL, bgcolor=bg))
    t.append(" " * inner, style=Style(bgcolor=bg))
    t.append(_V, style=Style(color=_BORDER, bgcolor=bg))

    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

