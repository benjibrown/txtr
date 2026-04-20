# build output panel - floating overlay showing compiler output
# opens on :build/:compile, streams lines as they arrive, q/escape to close
# press 'e' to switch to errors view and 'b' to go back - enter jumps to error :)
from __future__ import annotations

from textual.widget import Widget
from textual.strip import Strip
from rich.text import Text
from rich.style import Style
from rich.console import Console

from texitor.core.theme import theme as _theme

_BG = _theme.bg_alt
_BG_HEAD = _theme.bg_alt
_BG_SEL = _theme.bg_popup
_FG = _theme.fg
_FG_DIM = _theme.fg_dim
_GREEN = _theme.green
_RED = _theme.red
_YELLOW = _theme.yellow
_ACCENT = _theme.accent
_BORDER = _theme.border

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

_TL = "╭"; _TR = "╮"; _BL = "╰"; _BR = "╯"; _H = "─"; _V = "│"


def _strip(t, w):
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(w)


class BuildPanel(Widget):
    # floating panel that shows compiler output - 2 views
    # log - raw compiler output 
    # errors - parsed errors + warnings list

    DEFAULT_CSS = ""  # handled by app CSS

    def __init__(self, **kwargs):
        # W kwargs
        super().__init__(**kwargs)
        self._lines = []
        self._errors = []   # list[LogEntry] from parse_log
        self._scroll = 0
        self._status = "idle"   # idle | running | success | error
        self._engine = ""
        self._file = ""
        self._view = "log" # log | errors 
        self._err_cur = 0 # idx of selected error in view

    def reset(self, engine, filePath):
        self._lines  = []
        self._errors = []
        self._scroll = 0
        self._status = "running"
        self._engine = engine
        self._file   = filePath
        self._view = "log"
        self._err_cur = 0
        self.refresh()

    def appendLine(self, text, isErr=False, autoScroll=True):
        self._lines.append((text, isErr))
        if autoScroll:
            self._scroll = max(0, len(self._lines) - self._innerHeight())
        self.refresh()

    def setDone(self, returncode):
        self._status = "success" if returncode == 0 else "error"
        self.refresh()

    def setErrors(self, entries):
        self._errors = entries
        self.refresh()

    @property
    def errors(self):
        return self._errors

    # view switching 

    def showErrors(self):
        if self._errors:
            self._view = "errors"
            self._err_cur = 0
            self._scroll = 0
        self.refresh()

    def showLog(self):
        self._view = "log"
        self._scroll = max(0, len(self._lines) - self._innerHeight())
        self.refresh()

    # err cursor nav 

    def errCursorDown(self):
        if self._errors:
            self._err_cur = min(len(self._errors)-1, self._err_cur +1)
            self._clampErrScroll()
            self.refresh()

    def errCursorUp(self):
        if self._errors:
            self._err_cur = max(0, self._err_cur -1)
            self._clampErrScroll()
            self.refresh()

    def _clampErrScroll(self):
        ih = self._innerHeight()
        if self._err_cur < self._scroll:
            self._scroll = self._err_cur 
        elif self._err_cur >= self._scroll + ih:
            self._scroll = self._err_cur -ih + 1

    def selectedError(self):
        if self._view == "errors" and self._errors:
            return self._errors[self._err_cur]
        return None 

    # scroll stuff (log view)

    def scrollUp(self, n=3):
        if self._view == "errors":
            for _ in range(n): self.errCursorUp()
        else:
            self._scroll = max(0, self._scroll - n)
            self.refresh()

    def scrollDown(self, n=3):
        if self._view == "errors":
            for _ in range(n): self.errCursorDown()
        else:
            maxScroll = max(0, len(self._lines) - self._innerHeight())
            self._scroll = min(maxScroll, self._scroll + n)
            self.refresh()

    def _innerHeight(self):
        return max(1, self.size.height - 2)  # minus header + footer

    def get_content_height(self, container, viewport, width):
        return 30

    # rendering allat

    def render_line(self, y):
        w = self.size.width
        if w == 0:
            return Strip([])
        if y == 0:
            return self._renderHeader(w)
        if y == self.size.height - 1:
            return self._renderFooter(w)
        if self._view == "errors":
            return self._renderErrorLine(y -1 + self._scroll, w)
        lineIdx = y - 1 + self._scroll
        if lineIdx < len(self._lines):
            return self._renderOutputLine(self._lines[lineIdx], w)
        return self._renderEmpty(w)

    def _renderEmpty(self, w):
        t = Text(no_wrap=True)
        t.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        t.append(" " * max(0, w - 2), style=Style(bgcolor=_BG))
        t.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        return _strip(t,w)

    def _renderHeader(self, w):
        statusColor = {
            "running": _YELLOW,
            "success": _GREEN,
            "error":   _RED,
            "idle":    _FG_DIM,
        }.get(self._status, _FG_DIM)

        statusLabel = {
            "running": " compiling… ",
            "success": " success   ",
            "error":   " error     ",
            "idle":    " idle       ",
        }.get(self._status, "")

        fname = self._file.split("/")[-1] if self._file else ""
        if self._view == "errors":
            errs = sum(1 for e in self._errors if e.level == "error")
            warns = sum(1 for e in self._errors if e.level == "warning")
            tag = f" Errors  {errs}E {warns}W   {fname} "
        else:
            tag = f" Build  {self._engine}  {fname} "

        statusLen = len(statusLabel) + 2
        remaining = max(0, w - 2 - 2 - len(tag) - statusLen)

        t = Text(no_wrap=True)
        t.append(_TL + _H * 2, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
        t.append(tag, style=Style(color=_ACCENT, bgcolor=_BG_HEAD, bold=True))
        t.append(_H * remaining, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
        t.append(" " + statusLabel + " ", style=Style(color=statusColor, bgcolor=_BG_HEAD, bold=True))
        t.append(_TR, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
        return _strip(t, w)

    def _renderFooter(self, w):
        if self._view == "errors":
            hint = "   q/esc close    j/k nav    enter jump    b log  "
            total = len(self._errors)
            pos = f"   {self._err_cur +1}/{total} " if total else " 0 "
            mid = max(0, w-2-len(hint)-len(pos))
            t = Text(no_wrap=True)
            t.append(_BL, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
            t.append(hint, style=Style(color=_FG_DIM, bgcolor=_BG_HEAD))
            t.append(_H * mid, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
            t.append(pos, style=Style(color=_FG_DIM, bgcolor=_BG_HEAD))
            t.append(_BR, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
            return _strip(t,w)

        hint = "  q/esc close   j/k scroll  e errors  "
        total = len(self._lines)
        shown = min(self._scroll + self._innerHeight(), total)
        lineInfo = f" {self._scroll + 1}-{shown}/{total} " if total else " 0 lines "

        # error/warning summary from parsed log
        errs  = sum(1 for e in self._errors if e.level == "error")
        warns = sum(1 for e in self._errors if e.level == "warning")
        errInfo = ""
        if errs or warns:
            parts = []
            if errs: parts.append(f"{errs}E")
            if warns: parts.append(f"{warns}W")
            errInfo = "  " + " ".join(parts) + "  e --> errors"

        mid = max(0, w - 2 - len(hint) - len(lineInfo) - len(errInfo))

        t = Text(no_wrap=True)
        t.append(_BL, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
        t.append(hint, style=Style(color=_FG_DIM, bgcolor=_BG_HEAD))
        t.append(_H * mid, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
        if errInfo:
            ec = _RED if errs else _YELLOW
            t.append(errInfo, style=Style(color=ec, bgcolor=_BG_HEAD, bold=True))
        t.append(lineInfo, style=Style(color=_FG_DIM, bgcolor=_BG_HEAD))
        t.append(_BR, style=Style(color=_BORDER, bgcolor=_BG_HEAD))
        return _strip(t, w)
    
    def _renderErrorLine(self, idx ,w):
        if idx >= len(self._errors):
            return self._renderEmpty(w)

        entry = self._errors[idx]
        sel = (idx == self._err_cur)
        bg = _BG_SEL if sel else _BG 
        level_c = _RED if entry.level == "error" else _YELLOW 
        cursor = "❯ " if sel else "  "
        badge = "E" if entry.level == "error" else "W"

        loc = ""
        if entry.file:
            loc = entry.file.split("/")[-1]
        if entry.line is not None:
            loc += f":{entry.line}"

        inner = w-2 
        loc_w = min(18, max(8, inner - 28))
        msg_w = max(0, inner - loc_w - 5)
        loc_str = loc[:loc_w].ljust(loc_w)
        msg_str = entry.message[:msg_w]

        t = Text(no_wrap = True)
        t.append(_V, style=Style(color=_BORDER, bgcolor=bg))
        t.append(cursor, style=Style(color=level_c, bgcolor=bg, bold=sel))
        t.append(badge, style=Style(color=level_c, bgcolor=bg, bold=True))
        t.append(" ", style=Style(bgcolor=bg))
        t.append(loc_str, style=Style(color=_FG_DIM, bgcolor=bg))
        t.append(" ", style=Style(bgcolor=bg))
        t.append(msg_str, style=Style(color=_FG, bgcolor=bg, bold=sel))
        
        used = 4 + loc_w + len(msg_str)
        t.append(" " * max(0, inner-used), style=Style(bgcolor=bg))
        t.append(_V, style=Style(color=_BORDER, bgcolor=bg))
        return _strip(t, w)

    def _renderOutputLine(self, lineData, w):
        text, isErr = lineData
        if isErr or "error" in text.lower():
            fg = _RED
        elif "warning" in text.lower():
            fg = _YELLOW
        elif text.startswith("!"):
            fg = _RED
        elif text.startswith("Output written") or "successfully" in text.lower():
            fg = _GREEN
        else:
            fg = _FG

        inner = w - 2
        display = text[:inner] if len(text) > inner else text.ljust(inner)

        t = Text(no_wrap=True)
        t.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        t.append(display, style=Style(color=fg, bgcolor=_BG))
        t.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        return _strip(t, w)

