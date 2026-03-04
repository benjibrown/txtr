# widgets for editor

from __future__ import annotations
from typing import TYPE_CHECKING

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.buffer import Buffer
from texitor.core.modes import Mode, ModeStateMachine

if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

_CONSOLE = Console(
    width=500, no_color=False, highlight=False, markup=False, emoji=False
)

# color palette (catpuccin rn), will add this to config later so its easy to change
_BG           = "#1e1e2e"
_CURSORLINE   = "#252537"
_LINENUM_CUR  = "#cba6f7"   # mauve
_LINENUM_OFF  = "#585b70"   # overlay1
_GUTTER_SEP   = "#45475a"   # surface1
_TEXT         = "#cdd6f4"   # text
_TILDE        = "#45475a"
_CURSOR_BLOCK = {
    Mode.NORMAL:      ("#1e1e2e", "#89b4fa"),   # fg, bg — blue
    Mode.VISUAL:      ("#1e1e2e", "#cba6f7"),   # mauve
    Mode.VISUAL_LINE: ("#1e1e2e", "#cba6f7"),
}
_CURSOR_INSERT_FG = "#a6e3a1"   # cursor in insert mode
_SEL_BG           = "#45475a"   # surface1 - shows active line


class EditorWidget(Widget):

    DEFAULT_CSS = """
    EditorWidget {
        height: 1fr;
    }
    """

    def __init__(self, buf, msm, app):
        super().__init__()
        self._buf = buf
        self._msm = msm
        self._app = app
        self._scroll_top = 0

    # scrolling and whatnot
    def scroll_to_cursor(self):
        height = self.size.height
        if height <= 0:
            return
        row = self._buf.cursor_row
        if row < self._scroll_top:
            self._scroll_top = row
        elif row >= self._scroll_top + height:
            self._scroll_top = row - height + 1

    # rendering
    def render_line(self, y):
        buf = self._buf
        msm = self._msm
        width = self.size.width

        line_idx = self._scroll_top + y
        ln_w = max(len(str(buf.line_count)), 2)

        text = Text(no_wrap=True, overflow="ellipsis")

        # ── Beyond the buffer: single ~ on the first line past EOF (nvim style)
        if line_idx >= buf.line_count:
            if line_idx == buf.line_count:
                text.append(" " * (ln_w + 1))
                text.append("~", style=Style(color=_TILDE))
            return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)

        line = buf.lines[line_idx]
        is_current = line_idx == buf.cursor_row
        cur_bg = _CURSORLINE if (is_current and msm.is_normal()) else None
        
        # gutter
        ln_str = str(line_idx + 1).rjust(ln_w)
        if is_current:
            text.append(ln_str, style=Style(color=_LINENUM_CUR, bold=True, bgcolor=cur_bg))
        else:
            text.append(ln_str, style=Style(color=_LINENUM_OFF))
        text.append(" │ ", style=Style(color=_GUTTER_SEP, bgcolor=cur_bg))

        # content - no syntax highlighting for now
        content = Text(no_wrap=True)
        content.append(line, style=Style(color=_TEXT, bgcolor=cur_bg))
        

