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
from texitor.core.theme import theme as _theme
from texitor.core.config import config as cfg


if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

_CONSOLE = Console(
    width=500, no_color=False, highlight=False, markup=False, emoji=False
)

# colors - all sourced from the active theme
_BG           = _theme.bg
_CURSORLINE   = _theme.cursor_line
_LINENUM_CUR  = _theme.accent2
_LINENUM_OFF  = _theme.fg_muted
_GUTTER_SEP   = _theme.border
_TEXT         = _theme.fg
_TILDE        = _theme.border
_CURSOR_BLOCK = {
    Mode.NORMAL:      (_theme.bg, _theme.accent),
    Mode.VISUAL:      (_theme.bg, _theme.accent2),
    Mode.VISUAL_LINE: (_theme.bg, _theme.accent2),
}
_CURSOR_INSERT_FG = _theme.green
_SEL_BG   = _theme.bg_sel
_MATCH_BG = _theme.bg_search
_MATCH_FG = _theme.bg

# syntax highlight colors
_HL_CMD     = _theme.accent
_HL_ENV     = _theme.green
_HL_MATH    = _theme.orange
_HL_COMMENT = _theme.fg_muted
_HL_BRACE   = _theme.accent2


_INDENT_GUIDE = _theme.border   # subtle - same as border color


def _highlight(line, bg, tab_width=4, indent_guides=True):
    # tokenise and colour a single line of latex

    # indent guides - replace a space at each tab stop in leading whitespace with a visible bar
    guide_positions = set()
    if indent_guides and tab_width > 0:
        leading = len(line) - len(line.lstrip(" "))
        guide_positions = {p for p in range(tab_width, leading, tab_width) if p < len(line) and line[p] == " "}
        if guide_positions:
            chars = list(line)
            for p in guide_positions:
                chars[p] = "▎"
            line = "".join(chars)

    t = Text(no_wrap=True)
    t.append(line, style=Style(color=_TEXT, bgcolor=bg))

    def col(color, start, end):
        t.stylize(Style(color=color, bgcolor=bg), start, min(end, len(line)))

    # style guide chars (done after Text is built so they get the right color)
    for p in guide_positions:
        t.stylize(Style(color=_INDENT_GUIDE, bgcolor=bg), p, p + 1)

    # braces/brackets first (lowest priority - get overridden below where needed)
    for m in re.finditer(r'[{}\[\]]', line):
        col(_HL_BRACE, m.start(), m.end())

    # \commands
    for m in re.finditer(r'\\[a-zA-Z]+\*?', line):
        col(_HL_CMD, m.start(), m.end())

    # env name inside \begin{name} / \end{name} - override the plain text between braces
    for m in re.finditer(r'\\(?:begin|end)\{([^}]*)\}', line):
        name = m.group(1)
        brace_pos = line.index('{', m.start())
        col(_HL_ENV, brace_pos + 1, brace_pos + 1 + len(name))

    # math $...$ and $$...$$
    for m in re.finditer(r'\$\$.*?\$\$|\$[^$\n]*?\$', line):
        col(_HL_MATH, m.start(), m.end())

    # comments - % to end of line (skip escaped \%)
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


        self._visualLines = []
        self._wrapWidth = 0
    
    def _gutterWidth(self):
        ln_w = max(len(str(self._buf.line_count)),2)
        return ln_w + 3 

    def _contentwidth(self):
        w = self.size.width 
        if w <= 0:
            return 80 
        return max(1, w - self._gutterWidth())

    def rebuildVisualLines(self):
        wrap = cfg.get("editor", "wrap", True)
        contentW = self._contentwidth()
        self._wrapWidth = contentW 
        vlines = []
        if not wrap:
            for i in range(self._buf.line_count):
                vlines.append((i, 0))
        else:
            for i, line in enumerate(self._buf.lines):
                if not line:
                    vlines.append((i, 0))
                else:
                    col = 0
                    while col < len(line):
                        vlines.append((i, col))
                        col += contentW 
        self._visualLines = vlines

    def _cursorVisualRow(self):
        # grab the last visual row that starts at or before cursor_col on cursor_row 
        target_row = self._buf.cursor_row
        target_col = self._buf.cursor_col 
        best = 0
        for i, (li, cs) in enumerate(self._visualLines):
            if li == target_row and cs <= target_col:
                best = i 
            elif li > target_row:
                break 
        return best


    # scrolling and whatnot
    def scroll_to_cursor(self):
        height = self.size.height
        if height <= 0:
            return
        if not self._visualLines:
            self.rebuildVisualLines()
        vrow = self._cursorVisualRow()
        if vrow < self._scroll_top:
            self._scroll_top = vrow 
        elif vrow >= self._scroll_top + height:
            self._scroll_top = vrow - height + 1

    def on_resize(self, event):
        self.rebuildVisualLines()
        self.scroll_to_cursor()
        self.refresh()

    def on_mouse_scroll_down(self, event):
        step = 3
        maxScroll = max(0, len(self._visualLines) - 1)
        self._scroll_top = min(self._scroll_top + step, maxScroll)   
        self.refresh()

    def on_mouse_scroll_up(self, event):
        self._scroll_top = max(0, self._scroll_top - 3)
        self.refresh()

    def on_click(self, event):
        buf = self._buf 
        if not self._visualLines:
            self.rebuildVisualLines()
        gw = self._gutterWidth()
        vrow = self._scroll_top + event.y 
        if vrow >= len(self._visualLines):
            return 
        logical_idx, col_start = self._visualLines[vrow]                       
        clickedCol = col_start + max(0, event.x - gw)
        if logical_idx >= buf.line_count:
            return 
        buf.cursor_row = logical_idx 
        buf.cursor_col = min(clickedCol, max(0, len(buf.lines[logical_idx]), 1 ))
        if self._msm.is_insert():
            buf.cursor_col = min(clickedCol, len(buf.lines[logical_idx]))
            self._app._refresh_all()

    # rendering
    def render_line(self, y):
        buf = self._buf
        msm = self._msm
        width = self.size.width
        if not self._visualLines:
            self.rebuildVisualLines()

        vrow = self._scroll_top +y 
        ln_w = max(len(str(buf.line_count)), 2)
        gw = ln_w +3 
        contentW = max(1, width - gw)

        text = Text(no_wrap=True, overflow="ellipsis")
        # past end of all visual lines 
        if vrow >= len(self._visualLines):
            last_content_vrow = len(self._visualLines) - 1 
            if vrow == last_content_vrow +  1:
                text.append(" " * (ln_w + 1))
                text.append("~", style=Style(color=_TILDE))
            return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)

        logical_idx, col_start = self._visualLines[vrow]

        # sanity check 
        if logical_idx >= buf.line_count:
            return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)
        
        line        = buf.lines[logical_idx]
        is_first    = (col_start == 0)

        is_cursor_line = logical_idx == buf.cursor_row 
        cur_bg = _CURSORLINE if (is_cursor_line and msm.is_normal()) else None 

        # gutter - line number on first visual row only, blank on remaining rows 
        ln_str = str(logical_idx + 1).rjust(ln_w)
        if is_first:
            if is_cursor_line:
                text.append(ln_str, style=Style(color=_LINENUM_CUR, bold=True, bgcolor=cur_bg))
            else:
                text.append(ln_str, style=Style(color=_LINENUM_OFF))
        else:
            text.append(" " * ln_w, style=Style(bgcolor=cur_bg))
        text.append(" │ ", style=Style(color=_GUTTER_SEP, bgcolor=cur_bg))

        # logical line for this visual row 
        line_slice = line[col_start : col_start + contentW]

        tw = cfg.get("editor", "tab_width", 4)
        ig = cfg.get("editor", "indent_guides", True)

        # pass full line or idnent guide calc, then slice result 
        if is_first:
            content = _highlight(line_slice, cur_bg, tab_width=tw, indent_guides=ig)
        else:
            # no indent guides in cont rows 
            content = _highlight(line_slice, cur_bg, tab_width=tw, indent_guides=False) 

        # highlight search matches on this line - needs adjusting for col_start offset tho
        if self._app.searchMatches:
            for row, mc, length in self._app.searchMatches:
                if row == logical_idx:
                    s = mc - col_start 
                    e = s + length 
                    s = max(0, s)
                    e = min(contentW, e)

                    if s < e:
                        content.stylize(Style(color=_MATCH_FG, bgcolor=_MATCH_BG), s, e)

        # visual selection - adjst for col start
        anchor = self._app.visual_anchor
        if msm.is_visual() and anchor is not None:
            a_row, a_col = anchor
            c_row, c_col = buf.cursor_row, buf.cursor_col

            if msm.mode is Mode.VISUAL_LINE:
                r0, r1 = sorted((a_row, c_row))
                if r0 <= logical_idx <= r1:
                    content.stylize(Style(bgcolor=_SEL_BG), 0, max(len(line_slice), 1))
            else:
                if (a_row, a_col) <= (c_row, c_col):
                    r0, c0, r1, c1 = a_row, a_col, c_row, c_col
                else:
                    r0, c0, r1, c1 = c_row, c_col, a_row, a_col

                def toSlice(col):
                    return col - col_start 

                if r0 == r1 == logical_idx:
                    s = max(0, toSlice(c0))
                    e = min(contentW, toSlice(c1) + 1)

                    if s < e:
                        content.stylize(Style(bgcolor=_SEL_BG), s, e)
                elif logical_idx == r0:
                    s = max(0, toSlice(c0))
                    content.stylize(Style(bgcolor=_SEL_BG), s, max(len(line_slice), 1))

                elif r0 < logical_idx < r1:
                    content.stylize(Style(bgcolor=_SEL_BG), 0, max(len(line_slice), 1))
                elif logical_idx == r1:
                    e = min(contentW, toSlice(c1) + 1)
                    if e > 0:
                        content.stylize(Style(bgcolor=_SEL_BG), 0, e)

        # cursor - only on the visual row where it actually sits 
        if is_cursor_line and not msm.is_command():
            cur_col_in_slice = buf.cursor_col - col_start
            if 0 <= cur_col_in_slice <= contentW:
                if msm.is_insert():
                    s = Style(underline = True, bold = True, color=_CURSOR_INSERT_FG, bgcolor=cur_bg)
                    if cur_col_in_slice < len(content.plain):
                        content.stylize(s, cur_col_in_slice, cur_col_in_slice + 1)
                    else:
                        content.append(" ", style=s)
                else:
                    fg, bg = _CURSOR_BLOCK.get(msm.mode, ("#1e1e2e", "#fab387"))
                    s = Style(color=fg, bgcolor=bg, bold=True)

                    if cur_col_in_slice < len(content.plain):
                        content.stylize(s, cur_col_in_slice, cur_col_in_slice + 1)
                    else:
                        content.append(" ", style=s)
        
        text.append_text(content)

        if cur_bg:
            used = gw + len(line_slice)
            if used < width:
                text.append(" " * (width - used), style=Style(bgcolor=cur_bg))

        return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)


