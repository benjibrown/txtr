# incredibly peak file explorer
from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.theme import theme as _theme
from texitor.ui.editor import _highlight

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

_BG = _theme.bg
_BG_ALT = _theme.bg_alt
_BG_POP = _theme.bg_popup
_FG = _theme.fg
_FG_DIM = _theme.fg_dim
_FG_SUB = _theme.fg_sub
_ACC = _theme.accent
_ACC2 = _theme.accent2
_GREEN = _theme.green
_YELLOW = _theme.yellow
_BORDER = _theme.border
_SEL_BG = _theme.bg_sel

# TODO - make these constants lol 
_TL = "╭"; _TR = "╮"; _BL = "╰"; _BR = "╯"; _H = "─"; _V = "│" # i legit put this in every ui file
_MAX_W = 110
_MAX_H = 30


class FileExplorer(Widget):

    DEFAULT_CSS = """
    FileExplorer {
        layer: overlay;
        display: none;
        width: 110;
        height: 30;
    }
    """

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._cwd = Path.cwd()
        self._entries = []
        self._cursor = 0
        self._scrollTop = 0
        self._panelWidth = _MAX_W
        self._panelHeight = _MAX_H

    def open(self, start_path=None):
        base = Path(start_path).expanduser() if start_path else None
        if base and base.is_file():
            base = base.parent
        self._cwd = (base or self._cwd or Path.cwd()).resolve()
        self._reload()
        self._fitToScreen()
        self._center()
        self.display = True
        self.refresh()

    def close(self):
        self.display = False

    def relayout(self, size=None):
        self._fitToScreen(size)
        self._center(size)
        self.refresh()

    def on_resize(self, event):
        if self.display:
            self.relayout()

    def scrollDown(self, n=1):
        self._cursor = min(len(self._entries) - 1, self._cursor + n)
        self._revealCursor()
        self.refresh()

    def scrollUp(self, n=1):
        self._cursor = max(0, self._cursor - n)
        self._revealCursor()
        self.refresh()

    def parentDir(self):
        parent = self._cwd.parent
        if parent == self._cwd:
            return
        self._cwd = parent
        self._reload()

    # hopefully what each function does above is pretty self explanatory 

    def activateSelection(self):
        if not self._entries:
            return None
        kind, _, path = self._entries[self._cursor]
        if kind == "dir":
            self._cwd = path
            self._reload()
            return ("dir", str(path))
        if kind == "parent":
            self.parentDir()
            return ("dir", str(self._cwd))
        return ("file", str(path))

    def currentDir(self):
        return str(self._cwd)

    # reload the directory listing !!
    def _reload(self):
        self._entries = []
        if self._cwd.parent != self._cwd:
            self._entries.append(("parent", "..", self._cwd.parent))

        dirs = []
        files = []
        try:
            items = list(self._cwd.iterdir())
        except OSError:
            items = []

        for item in sorted(items, key=lambda p: (not p.is_dir(), p.name.lower())):
            if item.name.startswith("."):
                continue
            if item.is_dir():
                dirs.append(("dir", item.name + "/", item))
            else:
                files.append(("file", item.name, item))

        self._entries.extend(dirs + files)
        self._cursor = min(self._cursor, max(0, len(self._entries) - 1))
        self._scrollTop = 0
        self.refresh()

    def _center(self, size=None):
        screen = size or self.app.size
        self.styles.offset = (
            max(0, (screen.width - self._panelWidth) // 2),
            max(0, (screen.height - self._panelHeight) // 2),
        )

    def _fitToScreen(self, size=None):
        screen = size or self.app.size
        self._panelWidth = min(_MAX_W, max(44, screen.width - 2))
        self._panelHeight = min(_MAX_H, max(12, screen.height - 2))
        self.styles.width = self._panelWidth
        self.styles.height = self._panelHeight

    def _contentHeight(self):
        return max(1, self.size.height - 4)

    def _leftWidth(self):
        return max(24, min(42, self.size.width // 3))

    def _revealCursor(self):
        contentH = self._contentHeight()
        if self._cursor < self._scrollTop:
            self._scrollTop = self._cursor
        elif self._cursor >= self._scrollTop + contentH:
            self._scrollTop = self._cursor - contentH + 1

    # gen preview content for explorer
    def _previewRows(self, width, height):
        if not self._entries:
            return [Text(" empty directory ", style=Style(color=_FG_DIM, bgcolor=_BG))]

        kind, label, path = self._entries[self._cursor]
        if kind in ("dir", "parent"):
            rows = [
                Text(" directory ", style=Style(color=_ACC2, bgcolor=_BG, bold=True)),
                Text(str(path), style=Style(color=_FG_SUB, bgcolor=_BG)),
                Text(""),
            ]
            child_count = 0
            try:
                child_count = len([p for p in path.iterdir() if not p.name.startswith(".")])
            except OSError:
                pass
            rows.append(Text(f"{child_count} visible item{'s' if child_count != 1 else ''}", style=Style(color=_FG, bgcolor=_BG)))
            rows.append(Text(""))
            rows.append(Text("press enter or l to open this directory", style=Style(color=_GREEN, bgcolor=_BG)))
            rows.append(Text("press h or left to go to parent", style=Style(color=_FG_DIM, bgcolor=_BG)))
            return rows[:height]

        try:
            raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            return [
                Text(" preview unavailable ", style=Style(color=_YELLOW, bgcolor=_BG, bold=True)),
                Text(str(path), style=Style(color=_FG_SUB, bgcolor=_BG)),
            ]

        rows = [
            Text(path.name, style=Style(color=_ACC2, bgcolor=_BG, bold=True)),
            Text(str(path), style=Style(color=_FG_SUB, bgcolor=_BG)),
            Text(""),
        ]
        usable = max(0, height - len(rows))
        bodyW = max(1, width - 4)
        shown_lines = 0
        for idx, line in enumerate(raw, start=1):
            if len(rows) >= height:
                break
            line_no = Text(f"{idx:>3} ", style=Style(color=_FG_DIM, bgcolor=_BG))
            # preview should just look like syntax colour, not like the line got selected lol
            body = _highlight(line, _BG, indent_guides=False) if path.suffix == ".tex" else Text(line, style=Style(color=_FG, bgcolor=_BG))
            wrapped = _wrapPreviewText(body, bodyW)
            if not wrapped:
                wrapped = [Text("", style=Style(bgcolor=_BG))]
            for wrap_idx, chunk in enumerate(wrapped):
                if len(rows) >= height:
                    break
                row = Text()
                row.append_text(line_no if wrap_idx == 0 else Text("    ", style=Style(bgcolor=_BG)))
                row.append_text(chunk)
                rows.append(row)
            shown_lines = idx
        if len(raw) > shown_lines:
            rows.append(Text(" ...", style=Style(color=_FG_DIM, bgcolor=_BG)))
        return rows[:height]
    # holy peak method 
    def render_line(self, y):
        width = self.size.width
        inner = width - 2
        height = self.size.height
        leftW = self._leftWidth()
        rightW = max(1, inner - leftW - 1)

        if y == 0:
            return _renderTopBorder(width, inner, " file explorer ")
        if y == height - 3:
            return _renderDivider(width, inner)
        if y == height - 2:
            return _renderFooter(width, inner)
        if y == height - 1:
            return _renderBottomBorder(width, inner)

        contentY = y - 1
        rowIdx = self._scrollTop + contentY
        entry = self._entries[rowIdx] if rowIdx < len(self._entries) else None
        preview = self._previewRows(rightW - 1, self._contentHeight())
        previewRow = preview[contentY] if contentY < len(preview) else Text("")

        text = Text(no_wrap=True)
        text.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        text.append_text(_renderEntry(entry, rowIdx == self._cursor, leftW)) # yeah do cool stuff
        text.append("│", style=Style(color=_BORDER, bgcolor=_BG))

        text.append_text(_fitText(previewRow, rightW))
        text.append(_V, style=Style(color=_BORDER, bgcolor=_BG))
        return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)


def _renderEntry(entry, selected, width):
    bg = _SEL_BG if selected else _BG_ALT
    text = Text(no_wrap=True)
    if entry is None:
        text.append(" " * width, style=Style(bgcolor=bg))
        return text

    kind, label, _ = entry
    if kind == "dir":
        icon = " " # ts took so long to find 
        style = Style(color=_ACC, bgcolor=bg, bold=selected)
    elif kind == "parent":
        icon = "󰁍 "
        style = Style(color=_FG_SUB, bgcolor=bg, bold=selected)
    else:
        icon = "󰈔 "
        style = Style(color=_FG, bgcolor=bg, bold=selected)

    body = f" {icon}{label}" # is it a file? or  dir? or parent?
    text.append(body[:width], style=style)
    text.append(" " * max(0, width - len(body[:width])), style=Style(bgcolor=bg))

    return text



def _fitText(text, width):
    trimmed = text.copy()
    trimmed.truncate(width, overflow="crop", pad=True)
    return trimmed


def _wrapPreviewText(text, width):
    if width <= 0:
        return []
    wrapped = text.wrap(_CONSOLE, width, overflow="fold", no_wrap=False)
    rows = []
    for line in wrapped:
        row = Text()
        row.append_text(line)
        rows.append(_fitText(row, width))
    return rows


def _renderTopBorder(width, inner, title):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_TL, style=bs)
    t.append(_H, style=bs)
    t.append(title, style=Style(color=_ACC2, bgcolor=_BG, bold=True))
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


def _renderFooter(width, inner):
    hints = "  j/k move   enter/l open   h parent   : command   q close"
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_V, style=bs)
    t.append(hints[:inner], style=Style(color=_FG_DIM, bgcolor=_BG))
    t.append(" " * max(0, inner - len(hints[:inner])), style=Style(bgcolor=_BG))
    t.append(_V, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


def _renderBottomBorder(width, inner):
    t = Text(no_wrap=True)
    bs = Style(color=_BORDER, bgcolor=_BG)
    t.append(_BL, style=bs)
    t.append(_H * inner, style=bs)
    t.append(_BR, style=bs)
    return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    # reused a few methods from othe panels lmao - could centralise it
