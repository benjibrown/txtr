# widgets for editor

from __future__ import annotations
from typing import TYPE_CHECKING
import re

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
_BG = "#1e1e2e"
_CURSORLINE = "#252537"
_LINENUM_CUR = "#cba6f7"   # mauve
_LINENUM_OFF = "#585b70"   # overlay1
_GUTTER_SEP = "#45475a"   # surface1
_TEXT = "#cdd6f4"   # text
_TILDE = "#45475a"
_CURSOR_BLOCK = {
    Mode.NORMAL: ("#1e1e2e", "#89b4fa"),   # fg, bg — blue
    Mode.VISUAL: ("#1e1e2e", "#cba6f7"),   # mauve
    Mode.VISUAL_LINE: ("#1e1e2e", "#cba6f7"),
}
_CURSOR_INSERT_FG = "#a6e3a1"   # cursor in insert mode
_SEL_BG = "#45475a"   # surface1 - shows active line
_MATCH_BG = "#f9e2af"  # peach bg for search matches
_MATCH_FG = "#1e1e2e"  # dark text on peach
# i really do need to make theme config at some point, but for now this is fine

# syntax highlight colors
_HL_CMD     = "#89b4fa"   # blue   - \commands
_HL_ENV     = "#a6e3a1"   # green  - env names in \begin{}/\end{}
_HL_MATH    = "#fab387"   # peach  - $math$
_HL_COMMENT = "#585b70"   # muted  - % comments
_HL_BRACE   = "#cba6f7"   # mauve  - { } [ ]


def _highlight(line, bg):
    # tokenise and colour a single line of latex
    t = Text(no_wrap=True)
    t.append(line, style=Style(color=_TEXT, bgcolor=bg))

    def col(color, start, end):
        t.stylize(Style(color=color, bgcolor=bg), start, min(end, len(line)))

    # braces/brackets first (lowest priority — get overridden below where needed)
    for m in re.finditer(r'[{}\[\]]', line):
        col(_HL_BRACE, m.start(), m.end())

    # \commands
    for m in re.finditer(r'\\[a-zA-Z]+\*?', line):
        col(_HL_CMD, m.start(), m.end())

    # env name inside \begin{name} / \end{name} — override the plain text between braces
    for m in re.finditer(r'\\(?:begin|end)\{([^}]*)\}', line):
        name = m.group(1)
        brace_pos = line.index('{', m.start())
        col(_HL_ENV, brace_pos + 1, brace_pos + 1 + len(name))

    # math $...$ and $$...$$
    for m in re.finditer(r'\$\$.*?\$\$|\$[^$\n]*?\$', line):
        col(_HL_MATH, m.start(), m.end())

    # comments — % to end of line (skip escaped \%)
    cm = re.search(r'(?<!\\)%', line)
    if cm:
        col(_HL_COMMENT, cm.start(), len(line))

    return t
 

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

    def on_mouse_scroll_down(self, event):
        buf = self._buf
        step = 3
        self._scroll_top = min(self._scroll_top + step, max(0, buf.line_count - 1))
        self.refresh()

    def on_mouse_scroll_up(self, event):
        self._scroll_top = max(0, self._scroll_top - 3)
        self.refresh()

    def on_click(self, event):
        # click moves cursor - need to account for gutter width
        buf = self._buf
        ln_w = max(len(str(buf.line_count)), 2)
        gutterWidth = ln_w + 3  # "NNN │ "
        clickedRow = self._scroll_top + event.y
        clickedCol = max(0, event.x - gutterWidth)
        if clickedRow >= buf.line_count:
            return
        buf.cursor_row = clickedRow
        buf.cursor_col = min(clickedCol, max(0, len(buf.lines[clickedRow]) - 1))
        # click in normal mode just moves, click in insert mode allows free positioning
        if self._msm.is_insert():
            buf.cursor_col = min(clickedCol, len(buf.lines[clickedRow]))
        self._app._refresh_all()

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

        # syntax highlighted content — visual selection + cursor get layered on top
        content = _highlight(line, cur_bg)

        # highlight search matches on this line
        if self._app.searchMatches:
            for row, col, length in self._app.searchMatches:
                if row == line_idx:
                    content.stylize(Style(color=_MATCH_FG, bgcolor=_MATCH_BG), col, col + length)
        
        # highlight visual selection if in visual mode
        anchor = self._app.visual_anchor
        if msm.is_visual() and anchor is not None:
            a_row, a_col = anchor
            c_row, c_col = buf.cursor_row, buf.cursor_col

            if msm.mode is Mode.VISUAL_LINE:
                r0, r1 = sorted((a_row, c_row))
                if r0 <= line_idx <= r1:
                    content.stylize(Style(bgcolor=_SEL_BG), 0, max(len(line), 1))
            else:
                # character-wise: normalise so (r0,c0) ≤ (r1,c1)
                if (a_row, a_col) <= (c_row, c_col):
                    r0, c0, r1, c1 = a_row, a_col, c_row, c_col
                else:
                    r0, c0, r1, c1 = c_row, c_col, a_row, a_col

                if r0 == r1 == line_idx:
                    content.stylize(Style(bgcolor=_SEL_BG), c0, c1 + 1)
                elif line_idx == r0:
                    content.stylize(Style(bgcolor=_SEL_BG), c0, max(len(line), 1))
                elif r0 < line_idx < r1:
                    content.stylize(Style(bgcolor=_SEL_BG), 0, max(len(line), 1))
                elif line_idx == r1:
                    content.stylize(Style(bgcolor=_SEL_BG), 0, c1 + 1)

        if is_current and not msm.is_command():
            col = buf.cursor_col
            if msm.is_insert():
                s = Style(underline=True, bold=True,
                          color=_CURSOR_INSERT_FG, bgcolor=cur_bg)
                if col < len(content.plain):
                    content.stylize(s, col, col + 1)
                else:
                    content.append(" ", style=s)
            else:
                fg, bg = _CURSOR_BLOCK.get(msm.mode, ("#1e1e2e", "#fab387"))
                s = Style(color=fg, bgcolor=bg, bold=True)
                if col < len(content.plain):
                    content.stylize(s, col, col + 1)
                else:
                    content.append(" ", style=s)

        text.append_text(content)

        if cur_bg:
            gutter_len  = ln_w + 3
            content_len = len(line)
            used = gutter_len + content_len
            if used < width:
                text.append(" " * (width - used), style=Style(bgcolor=cur_bg))

        return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)


