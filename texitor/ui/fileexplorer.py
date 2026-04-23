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
    FileExplorer {}
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


