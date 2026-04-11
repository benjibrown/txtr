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

    DEFAULT_CSS = """"""
    InfoPanel {}
        layer: overlay;
        display: none;
        width: 76;
        height: 24;
    }
    """"""

    def __init__(self):
        super().__init__()
        self._title = " txtr info "
        self._footer = "  j/k scroll   q close"
        self._rows = []
        self._scrollTop = 0
        self._cursor = -1

    

