# help menu overlay - shows keybinds and snippets
# tab to switch between sections, q/escape to close
# plugins can register extra sections via HelpMenu.registerSection()

from __future__ import annotations
from typing import TYPE_CHECKING

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

# catppuccin colours
_BG          = "#1e1e2e"
_BG_HEADER   = "#181825"
_BG_ALT      = "#181825"   # alternate row bg for readability
_FG          = "#cdd6f4"
_FG_DIM      = "#6c7086"
_FG_KEY      = "#89b4fa"   # blue - keybind / trigger
_FG_ACTION   = "#cdd6f4"   # text - action description
_FG_SECTION  = "#cba6f7"   # mauve - section header
_FG_TAB_ACT  = "#1e1e2e"   # active tab fg
_BG_TAB_ACT  = "#89b4fa"   # active tab bg
_FG_TAB_IDLE = "#6c7086"
_BG_TAB_IDLE = "#313244"
_FG_SNIP_TRIG = "#a6e3a1"  # green - snippet trigger
_FG_SNIP_BODY = "#fab387"  # peach - snippet body preview
_FG_AUTO_BADGE = "#f9e2af" # yellow - auto badge

# extra sections registered by plugins - list of (title, callable -> list of rows)
# each row is either ("header", label) or ("row", left_col, right_col)
_PLUGIN_SECTIONS = []


def registerSection(title, rowsFn):
    # plugins call this to add a section to the help menu
    # rowsFn() should return a list of ("header", label) or ("row", left, right)
    _PLUGIN_SECTIONS.append((title, rowsFn))


def _keybindRows(keybinds):
    from texitor.core.modes import Mode
    rows = []
    modeOrder = [Mode.NORMAL, Mode.INSERT, Mode.VISUAL, Mode.VISUAL_LINE]
    modeLabels = {
        Mode.NORMAL:      "Normal",
        Mode.INSERT:      "Insert",
        Mode.VISUAL:      "Visual",
        Mode.VISUAL_LINE: "Visual Line",
    }
    for mode in modeOrder:
        binds = keybinds.all_for_mode(mode)
        if not binds:
            continue
        rows.append(("header", modeLabels[mode]))
        for key, action in sorted(binds.items()):
            # make the action name a bit more readable
            pretty = action.replace("_", " ")
            rows.append(("row", key, pretty))
    return rows


def _snippetRows(snippets):
    rows = []
    auto = {t: s for t, s in snippets._autoTriggers.items()}
    tab  = {t: s for t, s in snippets._tabTriggers.items()}

    if auto:
        rows.append(("header", "Auto triggers  (fire as you type)"))
        for trigger, snip in sorted(auto.items()):
            body = snip.get("body", "").replace("\n", " ↵ ")
            label = f"{snip.get('name', trigger)}  →  {body}"
            rows.append(("row", trigger, label))

    if tab:
        rows.append(("header", "Tab triggers  (shortcode + tab)"))
        for trigger, snip in sorted(tab.items()):
            body = snip.get("body", "").replace("\n", " ↵ ")
            label = f"{snip.get('name', trigger)}  →  {body}"
            rows.append(("row", trigger, label))

    return rows


class HelpMenu(Widget):

    DEFAULT_CSS = """
    HelpMenu {
        layer: overlay;
        display: none;
    }
    """

    def __init__(self, app):
        super().__init__()
        self._app = app
        # sections: list of (title, rowsFn)
        # rowsFn is called each time the menu opens so it's always fresh
        self._sections = [
            ("Keybinds",  lambda: _keybindRows(self._app.keybinds)),
            ("Snippets",  lambda: _snippetRows(self._app.snippets)),
        ]
        # add any plugin sections registered before the widget was created
        self._sections.extend(_PLUGIN_SECTIONS)
        self._activeTab = 0
        self._scrollTop = 0

    def registerSection(self, title, rowsFn):
        # add a section at runtime (eg from a plugin loaded after startup)
        self._sections.append((title, rowsFn))

    def open(self):
        self._activeTab = 0
        self._scrollTop = 0
        self._rows = self._buildRows()
        self.display = True
        self.refresh()

    def close(self):
        self.display = False
        self.refresh()

    def nextTab(self):
        self._activeTab = (self._activeTab + 1) % len(self._sections)
        self._scrollTop = 0
        self._rows = self._buildRows()
        self.refresh()

    def scrollDown(self, n=1):
        maxScroll = max(0, len(self._rows) - (self.size.height - 2))
        self._scrollTop = min(self._scrollTop + n, maxScroll)
        self.refresh()

    def scrollUp(self, n=1):
        self._scrollTop = max(0, self._scrollTop - n)
        self.refresh()

    def _buildRows(self):
        _, rowsFn = self._sections[self._activeTab]
        return rowsFn()

    # ── rendering ──────────────────────────────────────────────────────────────

    def get_content_height(self, container, viewport, width):
        return viewport.height

    def render_line(self, y):
        width = self.size.width
        height = self.size.height

        if y == 0:
            return self._renderTabBar(width)
        if y == height - 1:
            return self._renderFooter(width)

        # content rows
        contentY = y - 1
        rowIdx = self._scrollTop + contentY
        rows = getattr(self, "_rows", [])

        if rowIdx >= len(rows):
            t = Text(no_wrap=True)
            t.append(" " * width, style=Style(bgcolor=_BG))
            return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

        kind = rows[rowIdx][0]
        if kind == "header":
            return self._renderHeader(rows[rowIdx][1], width)
        return self._renderRow(rows[rowIdx][1], rows[rowIdx][2], rowIdx, width)

    def _renderTabBar(self, width):
        t = Text(no_wrap=True)
        t.append(" ", style=Style(bgcolor=_BG_HEADER))
        for i, (title, _) in enumerate(self._sections):
            if i == self._activeTab:
                t.append(f" {title} ", style=Style(color=_FG_TAB_ACT, bgcolor=_BG_TAB_ACT, bold=True))
            else:
                t.append(f" {title} ", style=Style(color=_FG_TAB_IDLE, bgcolor=_BG_TAB_IDLE))
            t.append(" ", style=Style(bgcolor=_BG_HEADER))
        # fill rest of bar
        t.append(" " * width, style=Style(bgcolor=_BG_HEADER))
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderHeader(self, label, width):
        t = Text(no_wrap=True)
        t.append(f"  {label}", style=Style(color=_FG_SECTION, bgcolor=_BG_ALT, bold=True))
        t.append(" " * width, style=Style(bgcolor=_BG_ALT))
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderRow(self, left, right, rowIdx, width):
        bg = _BG_ALT if rowIdx % 2 == 0 else _BG
        t = Text(no_wrap=True)
        t.append("  ", style=Style(bgcolor=bg))
        t.append(f"{left:<14}", style=Style(color=_FG_KEY, bgcolor=bg, bold=True))
        t.append("  ", style=Style(bgcolor=bg))
        # trim right col to fit
        available = width - 18
        trimmed = right[:available] if available > 0 else ""
        t.append(trimmed, style=Style(color=_FG_ACTION, bgcolor=bg))
        t.append(" " * width, style=Style(bgcolor=bg))
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderFooter(self, width):
        hints = "  tab  next tab    j/k  scroll    q / esc  close"
        t = Text(no_wrap=True)
        t.append(hints, style=Style(color=_FG_DIM, bgcolor=_BG_HEADER))
        t.append(" " * width, style=Style(bgcolor=_BG_HEADER))
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)
