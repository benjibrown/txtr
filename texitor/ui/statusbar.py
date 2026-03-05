# statusbar - mode pill, filename, position

from __future__ import annotations

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.buffer import Buffer
from texitor.core.modes import Mode, ModeStateMachine

_CONSOLE = Console(
    width=500, no_color=False, highlight=False, markup=False, emoji=False
)

# (label, fg, bg) per mode — catppuccin mocha, i will not apologize for this choice, catppuccin is love, catppuccin is life 
# TODO - configurable themes :)
_MODE_STYLE = {
    Mode.NORMAL:      ("NORMAL",      "#1e1e2e", "#89b4fa"),   # blue
    Mode.INSERT:      ("INSERT",      "#1e1e2e", "#a6e3a1"),   # green
    Mode.VISUAL:      ("VISUAL",      "#1e1e2e", "#cba6f7"),   # mauve
    Mode.VISUAL_LINE: ("VISUAL LINE", "#1e1e2e", "#cba6f7"),
    Mode.COMMAND:     ("COMMAND",     "#1e1e2e", "#f38ba8"),   # red
}

_BAR_BG  = "#181825"
_BAR_FG  = "#cdd6f4"
_POS_BG  = "#313244"


class StatusBar(Widget):

    DEFAULT_CSS = """
    StatusBar {
        height: 1;
        dock: bottom;
    }
    """

    def __init__(self, buf, msm):
        super().__init__()
        self._buf = buf
        self._msm = msm

    def render_line(self, y):
        if y != 0:
            return Strip.blank(self.size.width)

        buf = self._buf
        msm = self._msm
        width = self.size.width

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
