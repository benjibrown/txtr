# statusbar - mode pill, filename, position
# also doubles as input bar for COMMAND and SEARCH modes

from __future__ import annotations
from typing import TYPE_CHECKING

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.buffer import Buffer
from texitor.core.modes import Mode, ModeStateMachine
from texitor.core.theme import theme as _theme

if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

_CONSOLE = Console(
    width=500, no_color=False, highlight=False, markup=False, emoji=False
)

# colors - all sourced from the active theme
_MODE_STYLE = {
    Mode.NORMAL:      ("NORMAL",      _theme.bg, _theme.accent),
    Mode.INSERT:      ("INSERT",      _theme.bg, _theme.green),
    Mode.VISUAL:      ("VISUAL",      _theme.bg, _theme.accent2),
    Mode.VISUAL_LINE: ("VISUAL LINE", _theme.bg, _theme.accent2),
    Mode.COMMAND:     ("COMMAND",     _theme.bg, _theme.red),
    Mode.SEARCH:      ("SEARCH",      _theme.bg, _theme.accent),
}

_BAR_BG    = _theme.bg_alt
_BAR_FG    = _theme.fg
_POS_BG    = _theme.bg_popup
_CMD_FG    = _theme.red
_SEARCH_FG = _theme.accent


class StatusBar(Widget):

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
    }
    """

    def __init__(self, buf, msm, app):
        super().__init__()
        self._buf = buf
        self._msm = msm
        self._app = app

    def render_line(self, y):
        if y != 0:
            return Strip.blank(self.size.width)

        buf = self._buf
        msm = self._msm
        width = self.size.width

        # command mode - render as input bar
        if msm.mode is Mode.COMMAND:
            text = Text(no_wrap=True)
            text.append(":", style=Style(color=_CMD_FG, bgcolor=_BAR_BG, bold=True))
            text.append(self._app.cmd_input, style=Style(color=_BAR_FG, bgcolor=_BAR_BG))
            text.append(" ", style=Style(bgcolor=_CMD_FG))
            return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)

        # search mode - render as search bar
        if msm.mode is Mode.SEARCH:
            text = Text(no_wrap=True)
            prompt = "? " if self._app.searchBackward else "/ "
            text.append(prompt, style=Style(color=_SEARCH_FG, bgcolor=_BAR_BG, bold=True))
            text.append(self._app.searchPattern, style=Style(color=_BAR_FG, bgcolor=_BAR_BG))
            text.append(" ", style=Style(bgcolor=_SEARCH_FG))
            return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)

        label, fg, bg = _MODE_STYLE.get(msm.mode, ("???", _BAR_FG, _BAR_BG))

        text = Text(no_wrap=True)
        text.append(f" {label} ", style=Style(color=fg, bgcolor=bg, bold=True))

        name = buf.path or "[No Name]"
        if buf.modified:
            name += " ●"
        text.append(f"  {name}", style=Style(color=_BAR_FG, bgcolor=_BAR_BG))

        pos = f" {buf.cursor_row + 1}:{buf.cursor_col + 1} "
        used = (len(label) + 2) + (len(name) + 2) + len(pos)
        text.append(" " * max(0, width - used), style=Style(bgcolor=_BAR_BG))
        text.append(pos, style=Style(color=_BAR_FG, bgcolor=_POS_BG, bold=True))

        return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)
