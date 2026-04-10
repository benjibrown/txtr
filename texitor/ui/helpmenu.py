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

# colors - all sourced from the active theme
from texitor.core.theme import theme as _theme

_BG          = _theme.bg
_BG_ALT      = _theme.bg_alt
_FG_DIM      = _theme.fg_dim
_FG_KEY      = _theme.accent
_FG_ACTION   = _theme.fg
_FG_SECTION  = _theme.accent2
_FG_TAB_ACT  = _theme.bg
_BG_TAB_ACT  = _theme.accent
_FG_TAB_IDLE = _theme.fg_dim
_BG_TAB_IDLE = _theme.bg_popup
_BORDER      = _theme.border
_TITLE_FG    = _theme.accent2

# box drawing chars
_TL = "╭"
_TR = "╮"
_BL = "╰"
_BR = "╯"
_H  = "─"
_V  = "│"

# plugin sections registered before widget mounts
_PLUGIN_SECTIONS = []


def registerSection(title, rowsFn):
    # plugins call this to add a section to the help menu
    # rowsFn() returns list of ("header", label) or ("row", left, right)
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
    sections = [mode for mode in modeOrder if keybinds.all_for_mode(mode)]
    for i, mode in enumerate(sections):
        binds = keybinds.all_for_mode(mode)
        rows.append(("header", modeLabels[mode]))
        for key, action in sorted(binds.items()):
            rows.append(("row", key, action.replace("_", " ")))
        if i < len(sections) - 1:
            rows.append(("gap",))
    return rows


def _snippetRows(snippets):
    rows = []
    auto = dict(snippets._autoTriggers)
    tab  = dict(snippets._tabTriggers)
    if auto:
        rows.append(("header", "Auto triggers  (fire as you type)"))
        for trigger, snip in sorted(auto.items()):
            body = snip.get("body", "").replace("\n", " ↵ ")
            rows.append(("row", trigger, f"{snip.get('name', trigger)}  →  {body}"))
        if tab:
            rows.append(("gap",))
    if tab:
        rows.append(("header", "Tab triggers  (shortcode + tab)"))
        for trigger, snip in sorted(tab.items()):
            body = snip.get("body", "").replace("\n", " ↵ ")
            rows.append(("row", trigger, f"{snip.get('name', trigger)}  →  {body}"))
    return rows

from texitor.core.cmdregistry import registry as _cmdRegistry


def registerPluginCommands(pluginName, cmds):
    # plugins register their commands via the central registry
    # cmds is a list of (":cmd syntax", "description") tuples
    _cmdRegistry.registerSection(f"Plugin: {pluginName}", cmds)


def _commandRows():
    rows = []
    for section, cmds in _cmdRegistry.sections():
        rows.append(("header", section))
        for cmd, desc in cmds:
            rows.append(("row", cmd, desc))
        rows.append(("gap",))
    return rows


def _pluginRows():
    from texitor.core.plugins import pluginLoader, PLUGIN_DIR
    rows = []

    loaded = pluginLoader.loaded()
    if loaded:
        rows.append(("header", "Loaded plugins"))
        for name in sorted(loaded):
            inst = pluginLoader.get(name)
            ver = getattr(inst, "version", "") or ""
            author = getattr(inst, "author", "") or ""
            desc = getattr(inst, "description", "") or ""
            right = f"v{ver}" + (f"  by {author}" if author else "") + (f"  - {desc}" if desc else "")
            rows.append(("row", name, right))
    else:
        rows.append(("header", "Loaded plugins"))
        rows.append(("row", "(none)", "use :plugin enable <name> to load a plugin"))

    rows.append(("gap",))

    available = set(pluginLoader.availableOnDisk()) - set(loaded)
    if available:
        rows.append(("header", "Available (not loaded)"))
        for name in sorted(available):
            rows.append(("row", name, ":plugin enable " + name))
        rows.append(("gap",))

    rows.append(("header", "Commands"))
    rows.append(("row", ":plugin list", "show plugins in build panel"))
    rows.append(("row", ":plugin info <n>", "show full plugin info"))
    rows.append(("row", ":plugin enable <n>", "load a plugin + save to config"))
    rows.append(("row", ":plugin disable <n>", "unload a plugin + remove from config"))
    rows.append(("row", ":plugin install <n>", "download from registry and enable"))
    rows.append(("gap",))
    rows.append(("header", "Plugin directory"))
    rows.append(("row", str(PLUGIN_DIR), "drop .py files or git-cloned dirs here"))
    return rows


class HelpMenu(Widget):

    DEFAULT_CSS = """
    HelpMenu {
        layer: overlay;
        display: none;
        width: 84;
        height: 26;
    }
    """

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._sections = [
            ("Keybinds", lambda: _keybindRows(self._app.keybinds)),
            ("Snippets", lambda: _snippetRows(self._app.snippets)),
            ("Commands", _commandRows),
            ("Plugins", _pluginRows),
        ]
        self._sections.extend(_PLUGIN_SECTIONS)
        self._activeTab = 0
        self._scrollTop = 0
        self._rows = []
        self._tabRanges = []

    def registerSection(self, title, rowsFn):
        self._sections.append((title, rowsFn))

    def open(self):
        self._activeTab = 0
        self._scrollTop = 0
        self._rows = self._buildRows()
        self._tabRanges = []
        self._center()
        self.display = True
        self.refresh()

    def _center(self):
        # calculate offset to center the widget on screen
        screenW = self.app.size.width
        screenH = self.app.size.height
        x = max(0, (screenW - 84) // 2)
        y = max(0, (screenH - 26) // 2)
        self.styles.offset = (x, y)

    def on_resize(self, event):
        # re-center if terminal is resized while open
        if self.display:
            self._center()

    def close(self):
        self.display = False
        self.refresh()

    def nextTab(self):
        self._activeTab = (self._activeTab + 1) % len(self._sections)
        self._scrollTop = 0
        self._rows = self._buildRows()
        self.refresh()

    def scrollDown(self, n=1):
        # content area is height - 4 (top border + tab bar + footer + bottom border)
        maxScroll = max(0, len(self._rows) - (self.size.height - 4))
        self._scrollTop = min(self._scrollTop + n, maxScroll)
        self.refresh()

    def scrollUp(self, n=1):
        self._scrollTop = max(0, self._scrollTop - n)
        self.refresh()

    def on_mouse_scroll_down(self, event):
        self.scrollDown(3)

    def on_mouse_scroll_up(self, event):
        self.scrollUp(3)

    def on_click(self, event):
        # y=1 is the tab bar row (inside the top border)
        if event.y == 1:
            for start, end, idx in self._tabRanges:
                if start <= event.x < end:
                    self._activeTab = idx
                    self._scrollTop = 0
                    self._rows = self._buildRows()
                    self.refresh()
                    return

    def _buildRows(self):
        _, rowsFn = self._sections[self._activeTab]
        return rowsFn()

    # tuff as hell

    def get_content_height(self, container, viewport, width):
        return self.styles.height.value if self.styles.height else 26

    def render_line(self, y):
        width = self.size.width
        height = self.size.height
        inner = width - 2  # content width between borders

        if y == 0:
            return self._renderTopBorder(width, inner)
        if y == 1:
            return self._renderTabBar(width, inner)
        if y == 2:
            return self._renderDivider(width, inner)
        if y == height - 2:
            return self._renderDivider(width, inner)
        if y == height - 1:
            return self._renderFooter(width, inner)
        if y == height:
            return self._renderBottomBorder(width, inner)

        # content rows
        contentY = y - 3
        rowIdx = self._scrollTop + contentY
        if rowIdx >= len(self._rows):
            return self._renderBlankRow(width, inner)
        kind = self._rows[rowIdx][0]
        if kind == "header":
            return self._renderHeader(self._rows[rowIdx][1], width, inner)
        if kind == "gap":
            return self._renderBlankRow(width, inner)
        return self._renderRow(self._rows[rowIdx][1], self._rows[rowIdx][2], rowIdx, width, inner)

    def _renderTopBorder(self, width, inner):
        title = " txtr help "
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append(_TL, style=borderStyle)
        t.append(_H, style=borderStyle)
        t.append(title, style=Style(color=_TITLE_FG, bgcolor=_BG, bold=True))
        remaining = inner - 1 - len(title)
        t.append(_H * max(0, remaining), style=borderStyle)
        t.append(_TR, style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderTabBar(self, width, inner):
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append(_V, style=borderStyle)
        t.append(" ", style=Style(bgcolor=_BG))

        # track click regions - offset by 1 for the left border char
        self._tabRanges = []
        col = 2
        for i, (title, _) in enumerate(self._sections):
            tabWidth = len(title) + 2
            self._tabRanges.append((col, col + tabWidth, i))
            col += tabWidth + 1
            if i == self._activeTab:
                t.append(f" {title} ", style=Style(color=_FG_TAB_ACT, bgcolor=_BG_TAB_ACT, bold=True))
            else:
                t.append(f" {title} ", style=Style(color=_FG_TAB_IDLE, bgcolor=_BG_TAB_IDLE))
            t.append(" ", style=Style(bgcolor=_BG))

        # fill to right border
        t.append(" " * inner, style=Style(bgcolor=_BG))
        t.append(_V, style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderDivider(self, width, inner):
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append("├", style=borderStyle)
        t.append(_H * inner, style=borderStyle)
        t.append("┤", style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderBlankRow(self, width, inner):
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append(_V, style=borderStyle)
        t.append(" " * inner, style=Style(bgcolor=_BG))
        t.append(_V, style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderHeader(self, label, width, inner):
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append(_V, style=borderStyle)
        content = f"  {label}"
        t.append(content, style=Style(color=_FG_SECTION, bgcolor=_BG, bold=True))
        t.append(" " * max(0, inner - len(content)), style=Style(bgcolor=_BG))
        t.append(_V, style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)


    # not a single new line lmao
    def _renderRow(self, left, right, rowIdx, width, inner):
        bg = _BG_ALT if rowIdx % 2 == 0 else _BG
        borderStyle = Style(color=_BORDER, bgcolor=bg)
        t = Text(no_wrap=True)
        t.append(_V, style=borderStyle)
        t.append("  ", style=Style(bgcolor=bg))
        keyCol = f"{left:<14}"
        t.append(keyCol, style=Style(color=_FG_KEY, bgcolor=bg, bold=True))
        t.append("  ", style=Style(bgcolor=bg))
        available = inner - len(keyCol) - 4
        trimmed = right[:available] if available > 0 else ""
        t.append(trimmed, style=Style(color=_FG_ACTION, bgcolor=bg))
        t.append(" " * inner, style=Style(bgcolor=bg))  # flood fill then clamp
        t.append(_V, style=Style(color=_BORDER, bgcolor=bg))
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)
    
    # hints for footer cos people forget lol
    def _renderFooter(self, width, inner):
        hints = "  tab next tab   j/k scroll   q / esc close"
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append(_V, style=borderStyle)
        t.append(hints, style=Style(color=_FG_DIM, bgcolor=_BG))
        t.append(" " * max(0, inner - len(hints)), style=Style(bgcolor=_BG))
        t.append(_V, style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

    def _renderBottomBorder(self, width, inner):
        t = Text(no_wrap=True)
        borderStyle = Style(color=_BORDER, bgcolor=_BG)
        t.append(_BL, style=borderStyle)
        t.append(_H * inner, style=borderStyle)
        t.append(_BR, style=borderStyle)
        return Strip(list(t.render(_CONSOLE))).adjust_cell_length(width)

