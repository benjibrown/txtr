# autocomplete overlay widget
# renders a floating list of completions near the cursor
# knows nothing about the app - just takes a list of (cmd, desc) and selected index

from __future__ import annotations
from typing import TYPE_CHECKING

from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget
from rich.console import Console

if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

# colors - all sourced from the active theme
from texitor.core.theme import theme as _theme

_BG_NORMAL   = _theme.bg_popup
_BG_SELECTED = _theme.bg_sel
_FG_CMD      = _theme.accent
_FG_DESC     = _theme.fg_dim
_FG_SEL_CMD  = _theme.fg
_FG_SEL_DESC = _theme.fg_sub
_BORDER_COL  = _theme.fg_muted

MAX_VISIBLE = 8   # max rows shown at once


class AutocompleteWidget(Widget):

    DEFAULT_CSS = """
    AutocompleteWidget {
        width: 36;
        height: auto;
        layer: overlay;
        display: none;
    }
    """

    def __init__(self, app):
        super().__init__()
        self._app = app

    def on_mouse_scroll_down(self, event):
        if not self._app.acActive or not self._app.acItems:
            return
        self._app.acIndex = (self._app.acIndex + 1) % len(self._app.acItems)
        self._app._refreshAutocomplete()

    def on_mouse_scroll_up(self, event):
        if not self._app.acActive or not self._app.acItems:
            return
        self._app.acIndex = (self._app.acIndex - 1) % len(self._app.acItems)
        self._app._refreshAutocomplete()

    def on_click(self, event):
        # click an item to confirm it
        if not self._app.acActive or not self._app.acItems:
            return
        scrollTop = getattr(self, "_acScrollTop", 0)
        clickedIdx = scrollTop + event.y
        if clickedIdx < len(self._app.acItems):
            self._app.acIndex = clickedIdx
            self._app._confirmAutocomplete()
            self._app._refresh_all()

    def get_content_height(self, container, viewport, width):
        count = min(len(self._app.acItems), MAX_VISIBLE)
        return max(count, 1)

    def render_line(self, y):
        items = self._app.acItems
        selectedIdx = self._app.acIndex
        scrollTop = self._scrollTop()
        width = self.size.width

        itemIdx = scrollTop + y
        if itemIdx >= len(items):
            # blank padding row
            t = Text(no_wrap=True)
            t.append(" " * width, style=Style(bgcolor=_BG_NORMAL))
            return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

        cmd, desc = items[itemIdx]
        isSelected = itemIdx == selectedIdx

        bgColor = _BG_SELECTED if isSelected else _BG_NORMAL
        cmdColor = _FG_SEL_CMD if isSelected else _FG_CMD
        descColor = _FG_SEL_DESC if isSelected else _FG_DESC

        t = Text(no_wrap=True)
        # small left padding
        t.append(" ", style=Style(bgcolor=bgColor))
        t.append(cmd, style=Style(color=cmdColor, bgcolor=bgColor, bold=isSelected))

        # desc right-aligned with a gap
        gap = " "
        available = width - len(cmd) - 1 - len(gap)
        if available > 4:
            trimmedDesc = desc[:available]
            padding = available - len(trimmedDesc)
            t.append(gap + " " * padding, style=Style(bgcolor=bgColor))
            t.append(trimmedDesc, style=Style(color=descColor, bgcolor=bgColor, italic=True))
        else:
            remaining = width - len(cmd) - 1
            if remaining > 0:
                t.append(" " * remaining, style=Style(bgcolor=bgColor))

        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _scrollTop(self):
        # keep selected item in view
        idx = self._app.acIndex
        if not hasattr(self, "_acScrollTop"):
            self._acScrollTop = 0
        if idx < self._acScrollTop:
            self._acScrollTop = idx
        elif idx >= self._acScrollTop + MAX_VISIBLE:
            self._acScrollTop = idx - MAX_VISIBLE + 1
        return self._acScrollTop

    def resetScroll(self):
        self._acScrollTop = 0
