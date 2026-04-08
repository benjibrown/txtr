# txtr app package
# TxtrApp is the main application class.
# ActionsMixin  — all _action_* handler methods (actions.py)
# CommandsMixin — _action_execute_command, _cmd_* methods (commands.py)
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.events import Key

from texitor.core.buffer import Buffer
from texitor.core.keybinds import KeybindRegistry
from texitor.core.modes import Mode, ModeStateMachine
from texitor.core.firstrun import ensureUserConfig
from texitor.core.config import config as cfg
from texitor.core.clipboard import copyToSystem, pasteFromSystem
from texitor.core.theme import theme as _theme, getStartupWarning
from texitor.ui.editor import EditorWidget
from texitor.ui.statusbar import StatusBar
from texitor.ui.autocomplete import AutocompleteWidget
from texitor.ui.helpmenu import HelpMenu
from texitor.ui.configpanel import ConfigPanel
from texitor.ui.buildpanel import BuildPanel
from texitor.ui.splash import SplashWidget
import texitor.core.compiler as _compiler
import texitor.core.recents as _recents
from texitor.latex.snippets import SnippetManager
from texitor.latex.completer import LatexCompleter
from texitor.core.citecompleter import CiteCompleter

import re
_CITE_PAT = re.compile(r'\\cite[a-z*]*\{([^}]*)$')}')

from texitor.ui.app.actions import ActionsMixin
from texitor.ui.app.commands import CommandsMixin


# helpers!!
def _buildAppCss(t):
    return f"""
    Screen {{
        layers: base overlay;
        overflow: hidden hidden;
        scrollbar-size: 0 0;
    }}

    ToastRack {{
        align: right top;
        margin: 1 2;
    }}

    Toast {{
        background: {t.bg_popup};
        color: {t.fg};
        border-left: tall {t.accent};
        padding: 0 1;
    }}

    Toast.-warning {{
        border-left: tall {t.yellow};
        color: {t.yellow};
    }}

    Toast.-error {{
        border-left: tall {t.red};
        color: {t.red};
    }}

    Toast.-information {{
        border-left: tall {t.accent};
        color: {t.fg};
    }}

    AutocompleteWidget {{
        layer: overlay;
        width: 36;
        height: auto;
        display: none;
    }}

    HelpMenu {{
        layer: overlay;
        display: none;
    }}

    ConfigPanel {{
        layer: overlay;
        display: none;
    }}

    BuildPanel {{
        layer: overlay;
        display: none;
        width: 80%;
        height: 60%;
        offset-x: 10%;
        offset-y: 20%;
    }}

    SplashWidget {{
        layer: overlay;
        display: none;
        overflow: hidden hidden;
    }}
    """


def _coerceValue(raw):
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try: 
        return int(raw)
    except ValueError: 
        pass
    try: 
        return float(raw)
    except ValueError: 
        pass
    return raw


def _resolveConfigKey(dotKey):
    if "." in dotKey:
        section, key = dotKey.split(".", 1)
        return (section, key)
    for section, values in cfg.all().items():
        if dotKey in values:
            return (section, dotKey)
    return (None, None)


def _tabStr():
    return " " * cfg.get("editor", "tab_width", 4)


def _useSystemClip():
    return cfg.get("editor", "system_clipboard", False)



# the main app - W class
class TxtrApp(ActionsMixin, CommandsMixin, App):

    TITLE = "txtr"
    ENABLE_COMMAND_PALETTE = False
    CSS = _buildAppCss(_theme)

    def __init__(self, filename=None):
        super().__init__()
        self.buffer = Buffer()
        self.msm = ModeStateMachine()
        self.keybinds = KeybindRegistry()
        self._yank = []
        self.visual_anchor = None

        self.cmd_input = ""
        self.searchPattern = ""
        self.searchMatches = []
        self.searchIndex = 0
        self.searchBackward = False
        self._pending_key = ""
        self._awaiting_replace = False

        self.tabStops = []
        self.tabStopIdx = 0
        self._lastTabRow = 0
        self._lastTabCol = 0
        self._lastTabLength = 0
        self._justExpanded = False
        self._revertCount = 0

        self.acItems = []
        self.acIndex = 0
        self.acActive = False
        self.acPrefix = ""

        self.splashOpen = (filename is None)
        self.helpOpen   = False
        self.configOpen = False
        self.buildOpen  = False
        self._buildTask = None
        self._buildPrimed = False
        self._buildStatus = ""

        self.snippets  = SnippetManager()
        self.completer = LatexCompleter()
        self.citeCompleter = CiteCompleter()

        ensureUserConfig()
        cfg.load()
        self.snippets.load()
        self.completer.load()

        if filename:
            self.buffer.load(filename)
            _recents.push(filename)
            self._loadBibsForFile(filename)

    def compose(self) -> ComposeResult: # peak
        yield EditorWidget(self.buffer, self.msm, self)
        yield AutocompleteWidget(self)
        yield HelpMenu(self)
        yield ConfigPanel()
        yield BuildPanel()
        yield SplashWidget(self)
        yield StatusBar(self.buffer, self.msm, self)

    def on_mount(self):
        self._registerCommands()
        warn = getStartupWarning()
        if warn:
            self.notify(warn, severity="warning", timeout=6)
        if self.splashOpen:
            splash = self.query_one(SplashWidget)
            splash.refresh_recents()
            splash.reposition()
            splash.display = True

    def _dismissSplash(self):
        self.splashOpen = False
        self.query_one(SplashWidget).display = False
        self._refresh_all()

    def on_resize(self, event):
        if self.splashOpen:
            self.query_one(SplashWidget).reposition()

    # key dispatch stuff
    def on_key(self, event: Key):
        event.stop()
        event.prevent_default()

        key = event.key

        # splash screen swallows all keys
        if self.splashOpen:
            splash = self.query_one(SplashWidget)
            if key in ("j", "down"):
                splash.cursor_down()
            elif key in ("k", "up"):
                splash.cursor_up()
            elif key == "enter":
                path = splash.selected_recent()
                if path:
                    self._dismissSplash()
                    self.buffer.load(path)
                    _recents.push(path)
                    self._refresh_all()
                else:
                    self._dismissSplash()
            elif key == "q":
                self.exit()
            elif key == "e":
                self._dismissSplash()
            elif key == "colon" or event.character == ":":
                self._dismissSplash()
                self._action_enter_command()
                self._refresh_all()
            else:
                self._dismissSplash()
            return

        # overlays swallow keys while open
        if self.helpOpen:
            if self.msm.is_command():
                pass
            elif key in ("q", "escape"):
                self._action_close_help()
                return
            elif key == "colon" or event.character == ":":
                self._action_enter_command()
                self._refresh_all()
                return
            elif key == "tab":
                self.query_one(HelpMenu).nextTab()
                return
            elif key in ("j", "down"):
                self.query_one(HelpMenu).scrollDown()
                return
            elif key in ("k", "up"):
                self.query_one(HelpMenu).scrollUp()
                return
            elif key == "ctrl+d":
                self.query_one(HelpMenu).scrollDown(8)
                return
            elif key == "ctrl+u":
                self.query_one(HelpMenu).scrollUp(8)
                return
            else:
                return

        if self.configOpen:
            if self.msm.is_command():
                pass
            elif key in ("q", "escape"):
                self.configOpen = False
                self.query_one(ConfigPanel).close()
                return
            elif key == "colon" or event.character == ":":
                self._action_enter_command()
                self._refresh_all()
                return
            elif key in ("j", "down"):
                self.query_one(ConfigPanel).scrollDown()
                return
            elif key in ("k", "up"):
                self.query_one(ConfigPanel).scrollUp()
                return
            elif key == "ctrl+d":
                self.query_one(ConfigPanel).scrollDown(8)
                return
            elif key == "ctrl+u":
                self.query_one(ConfigPanel).scrollUp(8)
                return
            else:
                return

        if self.buildOpen:
            panel = self.query_one(BuildPanel)
            if key in ("q", "escape"):
                self.buildOpen = False
                panel.display = False
                return
            elif key in ("j", "down"):
                panel.scrollDown()
                return
            elif key in ("k", "up"):
                panel.scrollUp()
                return
            elif key == "ctrl+d":
                panel.scrollDown(8)
                return
            elif key == "ctrl+u":
                panel.scrollUp(8)
                return
            elif key == "e":
                panel.showErrors()
                return
            elif key == "b":
                panel.showLog()
                return
            elif key == "enter":
                entry = panel.selectedError()
                if entry and entry.line is not None:
                    self.buffer.cursor_row = max(0, min(entry.line - 1, len(self.buffer.lines) - 1))
                    self.buffer.cursor_col = 0
                    self._refresh_all()
                    self.notify(f"jumped to l.{entry.line}", timeout=2)
                return
            else:
                return

        # replace-char mode
        if self._awaiting_replace:
            self._awaiting_replace = False
            if event.character and event.character.isprintable():
                buf  = self.buffer
                line = buf.current_line
                if buf.cursor_col < len(line):
                    buf.checkpoint()
                    buf.lines[buf.cursor_row] = (
                        line[: buf.cursor_col]
                        + event.character
                        + line[buf.cursor_col + 1:]
                    )
                    buf.modified = True
            self._refresh_all()
            return

        mode = self.msm.mode
        char = event.character or ""
        candidate = (self._pending_key + " " + key).strip()

        char_candidate = (self._pending_key + " " + char).strip() if char else ""

        action = self.keybinds.get(mode, candidate) or (
            self.keybinds.get(mode, char_candidate) if char_candidate else None
        )
        if action:
            self._pending_key = ""
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler()
            self._refresh_all()
            return

        if self._is_prefix(mode, candidate) or (char_candidate and self._is_prefix(mode, char_candidate)):
            self._pending_key = candidate
            return

        self._pending_key = ""
        action = self.keybinds.get(mode, key) or (self.keybinds.get(mode, char) if char else None)
        if action:
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler()
            self._refresh_all()
            return

        if self.msm.is_insert() and event.character and event.character.isprintable():
            self._justExpanded = False
            self.buffer.checkpoint()
            self._insertWithAutoPairs(event.character)
            self._checkSnippetTrigger()
            self._updateAutocomplete()
            self._refresh_all()

        elif self.msm.is_command():
            if key == "backspace":
                self.cmd_input = self.cmd_input[:-1]
                self.query_one(StatusBar).refresh()
            elif event.character and event.character.isprintable():
                self.cmd_input += event.character
                self.query_one(StatusBar).refresh()

        elif self.msm.is_search():
            if key == "backspace":
                self.searchPattern = self.searchPattern[:-1]
                self.query_one(StatusBar).refresh()
            elif event.character and event.character.isprintable():
                self.searchPattern += event.character
                self.query_one(StatusBar).refresh()



    # auto trigger for snippets :)
    def _checkSnippetTrigger(self):
        buf = self.buffer
        textBefore = buf.current_line[:buf.cursor_col]
        trigger, snippet = self.snippets.findAutoTrigger(textBefore)
        if trigger and snippet:
            body = snippet.get("body", "")
            buf.checkpoint()
            self.tabStops = self.snippets.expandInBuffer(trigger, body, buf)
            self.tabStopIdx = 0
            self._justExpanded = True
            self._revertCount = 1
            if self.tabStops:
                row, col, length = self.tabStops[0]
                buf.move_to(row, col)
                self._lastTabRow, self._lastTabCol, self._lastTabLength = row, col, length
                self.tabStopIdx = 1

    def _is_prefix(self, mode, prefix):
        return any(
            seq == prefix or seq.startswith(prefix + " ")
            for seq in self.keybinds.all_for_mode(mode)
        )

    # used everywhere - refresh editor + bar
    def _refresh_all(self):
        editor = self.query_one(EditorWidget)
        editor.rebuildVisualLines()
        editor.scroll_to_cursor()
        editor.refresh()
        self.query_one(StatusBar).refresh()
        if self.acActive:
            self._refreshAutocomplete()


    # bib helpers
    def _loadBibsForFile(self, filepath):
        from pathlib import Path
        p = Path(filepath).expanduser().resolve()
        extra = cfg.get("citations", "bib_files", [])
        self.citeCompleter.loadDir(p.parent, extra_paths=extra)
        n = self.citeCompleter.entryCount()
        if n:
            self.notify(f"loaded {n} bib entr{'y' if n == 1 else 'ies'}", severity="information")

    # autocomplete stuff
    def _updateAutocomplete(self):
        textBefore = self.buffer.current_line[:self.buffer.cursor_col]

        # cite context: \cite{, \citep{, \citet{, etc.}}}
        cm = _CITE_PAT.search(textBefore)
        if cm:
            prefix = cm.group(1)
            items = self.citeCompleter.getCompletions(prefix)
            if items:
                self.acItems = items
                self.acIndex = 0
                self.acPrefix = prefix
                self.acActive = True
                ac = self.query_one(AutocompleteWidget)
                ac.resetScroll()
                self._positionAutocomplete(wide=True)
                ac.display = True
                return
            self._dismissAutocomplete()
            return

        idx = len(textBefore) - 1
        while idx >= 0 and (textBefore[idx].isalpha() or textBefore[idx] == "\\"):
            if textBefore[idx] == "\\":
                prefix = textBefore[idx:]
                items  = self.completer.getCompletions(prefix)
                if items:
                    self.acItems = items
                    self.acIndex = 0
                    self.acPrefix = prefix
                    self.acActive = True
                    ac = self.query_one(AutocompleteWidget)
                    ac.resetScroll()
                    self._positionAutocomplete()
                    ac.display = True
                    return
                break
            idx -= 1
        self._dismissAutocomplete()

    def _positionAutocomplete(self, wide=False):
        editor = self.query_one(EditorWidget)
        buf = self.buffer
        ac = self.query_one(AutocompleteWidget)

        gutterWidth = max(len(str(buf.line_count)), 2) + 3
        screenRow   = buf.cursor_row - editor._scroll_top
        screenCol   = gutterWidth + buf.cursor_col - len(self.acPrefix)

        editorHeight = editor.size.height
        popupHeight  = min(len(self.acItems), 8)
        row = screenRow + 1
        if row + popupHeight > editorHeight:
            row = max(0, screenRow - popupHeight)
        col = max(0, screenCol)

        ac.styles.width = 58 if wide else 36
        ac.styles.offset = (col, row)

    def _refreshAutocomplete(self):
        self._positionAutocomplete()
        self.query_one(AutocompleteWidget).refresh()

    def _dismissAutocomplete(self):
        self.acActive = False
        self.acItems = []
        self.acIndex = 0
        self.acPrefix = ""
        try:
            ac = self.query_one(AutocompleteWidget)
            ac.display = False
            ac.refresh()
        except Exception:
            pass

    def _confirmAutocomplete(self):
        if not self.acActive or not self.acItems:
            return
        cmd, _ = self.acItems[self.acIndex]
        buf = self.buffer
        col = buf.cursor_col
        line = buf.lines[buf.cursor_row]
        buf.lines[buf.cursor_row] = line[:col - len(self.acPrefix)] + line[col:]
        buf.cursor_col = col - len(self.acPrefix)
        buf.checkpoint()
        buf.insert(cmd)
        buf.modified = True
        self._dismissAutocomplete()
