# main app.
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
import texitor.core.compiler as _compiler
from texitor.latex.snippets import SnippetManager
from texitor.latex.completer import LatexCompleter


def _buildAppCss(t):
    # generate the app CSS from the active theme
    return f"""
    Screen {{
        layers: base overlay;
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
    """



def _coerceValue(raw):
    # coerce string config values to proper python types
    if raw.lower() == "true":  return True
    if raw.lower() == "false": return False
    try:                       return int(raw)
    except ValueError:         pass
    try:                       return float(raw)
    except ValueError:         pass
    return raw


def _resolveConfigKey(dotKey):
    # accepts "section.key" or bare "key" (searches all sections)
    # returns (section, key) or (None, None) if not found
    from texitor.core.config import config as cfg
    if "." in dotKey:
        section, key = dotKey.split(".", 1)
        return (section, key)
    # bare key - find which section it lives in
    for section, values in cfg.all().items():
        if dotKey in values:
            return (section, dotKey)
    return (None, None)


def _tabStr():
    # get the indent string based on config tab_width
    from texitor.core.config import config as cfg
    return " " * cfg.get("editor", "tab_width", 4)


def _useSystemClip():
    return cfg.get("editor", "system_clipboard", False)


class TxtrApp(App):
    # main app class - the big boy class that holds all of my janky code together...
    # i just realised how ridicously long this file is - a fair bit came from the textual boilerplate and the rest is me just being really inefficient :)

    TITLE = "txtr" # aka texitor but who wants to type allat
    ENABLE_COMMAND_PALETTE = False
    CSS = _buildAppCss(_theme)

    def __init__(self, filename=None):
        super().__init__()
        self.buffer = Buffer()
        self.msm = ModeStateMachine()
        self.keybinds = KeybindRegistry()
        self._yank = []
        self.visual_anchor = None
        # search and command input states 
        self.cmd_input = ""
        self.searchPattern = ""
        self.searchMatches = []    # list of (row, col, length) for all matches
        self.searchIndex = 0       # current match index
        self.searchBackward = False
        self._pending_key = ""
        self._awaiting_replace = False
        self.tabStops = []
        self.tabStopIdx = 0
        self._lastTabRow = 0   # row we jumped to for the current stop
        self._lastTabCol = 0   # col we jumped to for the current stop
        self._justExpanded = False
        self._revertCount = 0

        # autocomplete state
        self.acItems = []
        self.acIndex = 0
        self.acActive = False
        self.acPrefix = ""

        # help menu state
        self.helpOpen   = False
        self.configOpen = False
        self.buildOpen  = False
        self._buildTask = None

        self.snippets = SnippetManager()
        self.completer = LatexCompleter()

        # seed ~/.config/txtr/ with defaults on first run, then load
        ensureUserConfig()
        cfg.load()
        self.snippets.load()
        self.completer.load()

        if filename:
            self.buffer.load(filename)

    # layout of app (editor + bar)
    def compose(self):
        yield EditorWidget(self.buffer, self.msm, self)
        yield AutocompleteWidget(self)
        yield HelpMenu(self)
        yield ConfigPanel()
        yield BuildPanel()
        yield StatusBar(self.buffer, self.msm, self)

    def on_mount(self):
        # show any theme loading warning from startup
        warn = getStartupWarning()
        if warn:
            self.notify(warn, severity="warning", timeout=6)

    # key handling
    def on_key(self, event: Key):
        event.stop()
        event.prevent_default()

        key = event.key

        # help menu swallows most keys while open
        # but : and escape-from-command fall through so user can type commands while reading help
        if self.helpOpen:
            if self.msm.is_command():
                pass  # fall through to command mode handling below
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

        # config panel swallows most keys while open, same deal
        if self.configOpen:
            if self.msm.is_command():
                pass  # fall through to command mode handling below
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

        # build panel swallows keys while open
        if self.buildOpen:
            if key in ("q", "escape"):
                self.buildOpen = False
                self.query_one(BuildPanel).display = False
                return
            elif key in ("j", "down"):
                self.query_one(BuildPanel).scrollDown()
                return
            elif key in ("k", "up"):
                self.query_one(BuildPanel).scrollUp()
                return
            elif key == "ctrl+d":
                self.query_one(BuildPanel).scrollDown(8)
                return
            elif key == "ctrl+u":
                self.query_one(BuildPanel).scrollUp(8)
                return
            else:
                return

        # replace_char mode
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
                        + line[buf.cursor_col + 1 :]
                    )
                    buf.modified = True
            self._refresh_all()
            return

        # key handling for cmds with multiple keys ie gg or my favourite - dd
        # event.key gives textual's name (e.g. "colon" for :, "dollar_sign" for $)
        # event.character gives the actual char - we try both so keybinds.py can use either
        mode = self.msm.mode
        char = event.character or ""
        candidate = (self._pending_key + " " + key).strip()
        char_candidate = (self._pending_key + " " + char).strip() if char else ""

        action = self.keybinds.get(mode, candidate) or (self.keybinds.get(mode, char_candidate) if char_candidate else None)
        if action:
            self._pending_key = ""
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler()
            self._refresh_all()
            return

        # wait for more keys if needed
        if self._is_prefix(mode, candidate) or (char_candidate and self._is_prefix(mode, char_candidate)):
            self._pending_key = candidate
            return

        # if not then just try the single key
        self._pending_key = ""
        action = self.keybinds.get(mode, key) or (self.keybinds.get(mode, char) if char else None)
        if action:
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler()
            self._refresh_all()
            return

        # insert mode - any chars printable 
        if self.msm.is_insert() and event.character and event.character.isprintable():
            self._justExpanded = False
            self.buffer.checkpoint()
            self._insertWithAutoPairs(event.character)
            self._checkSnippetTrigger()
            self._updateAutocomplete()
            self._refresh_all()

        # command mode - type into cmd_input, backspace to delete
        elif self.msm.is_command():
            if key == "backspace":
                self.cmd_input = self.cmd_input[:-1]
                self.query_one(StatusBar).refresh()
            elif event.character and event.character.isprintable():
                self.cmd_input += event.character
                self.query_one(StatusBar).refresh()

        # search mode - type into searchPattern, backspace to delete
        elif self.msm.is_search():
            if key == "backspace":
                self.searchPattern = self.searchPattern[:-1]
                self.query_one(StatusBar).refresh()
            elif event.character and event.character.isprintable():
                self.searchPattern += event.character
                self.query_one(StatusBar).refresh()

    def _checkSnippetTrigger(self):
        buf = self.buffer
        textBefore = buf.current_line[:buf.cursor_col]
        trigger, snippet = self.snippets.findAutoTrigger(textBefore)
        if trigger and snippet:
            body = snippet.get("body", "")
            # checkpoint here - buffer currently has the full trigger typed,
            # so one undo will restore exactly back to it
            buf.checkpoint()
            self.tabStops = self.snippets.expandInBuffer(trigger, body, buf)
            self.tabStopIdx = 0
            self._justExpanded = True
            self._revertCount = 1
            if self.tabStops:
                row, col = self.tabStops[0]
                buf.move_to(row, col)
                self._lastTabRow, self._lastTabCol = row, col
                self.tabStopIdx = 1

    def _is_prefix(self, mode, prefix):
        return any(
            seq == prefix or seq.startswith(prefix + " ")
            for seq in self.keybinds.all_for_mode(mode)
        )

    def _refresh_all(self):
        editor = self.query_one(EditorWidget)
        editor.scroll_to_cursor()
        editor.refresh()
        self.query_one(StatusBar).refresh()
        if self.acActive:
            self._refreshAutocomplete()

    # autocomplete helpers
    # so peak - proud of this frfr
    def _updateAutocomplete(self):
        # called after every insert/backspace - opens or updates the popup
        textBefore = self.buffer.current_line[:self.buffer.cursor_col]

        # find the \prefix at the end of the line (eg \fra, \alp)
        idx = len(textBefore) - 1
        while idx >= 0 and (textBefore[idx].isalpha() or textBefore[idx] == "\\"):
            if textBefore[idx] == "\\":
                prefix = textBefore[idx:]
                items = self.completer.getCompletions(prefix)
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

        # nothing to show - dismiss
        self._dismissAutocomplete()

    def _positionAutocomplete(self):
        # position the popup just below the cursor in the editor
        editor = self.query_one(EditorWidget)
        buf = self.buffer
        ac = self.query_one(AutocompleteWidget)

        # figure out the cursor's screen position
        gutterWidth = max(len(str(buf.line_count)), 2) + 3  # "NNN │ "
        screenRow = buf.cursor_row - editor._scroll_top
        screenCol = gutterWidth + buf.cursor_col - len(self.acPrefix)

        # clamp so it doesn't go off-screen
        editorHeight = editor.size.height
        popupHeight = min(len(self.acItems), 8)
        row = screenRow + 1
        if row + popupHeight > editorHeight:
            row = max(0, screenRow - popupHeight)

        col = max(0, screenCol)

        ac.styles.offset = (col, row)

    def _refreshAutocomplete(self):
        ac = self.query_one(AutocompleteWidget)
        self._positionAutocomplete()
        ac.refresh()

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
            pass  # widget not mounted yet

    def _confirmAutocomplete(self):
        # insert the selected completion, replacing the prefix already typed
        if not self.acActive or not self.acItems:
            return
        cmd, _ = self.acItems[self.acIndex]
        buf = self.buffer
        col = buf.cursor_col
        # remove the prefix already in the buffer
        line = buf.lines[buf.cursor_row]
        buf.lines[buf.cursor_row] = line[:col - len(self.acPrefix)] + line[col:]
        buf.cursor_col = col - len(self.acPrefix)
        buf.checkpoint()
        buf.insert(cmd)
        buf.modified = True
        self._dismissAutocomplete()

    # mode trans 
    def _action_enter_normal(self):
        # if autocomplete is open, escape just dismisses it (stay in insert)
        if self.acActive:
            self._dismissAutocomplete()
            self._refresh_all()
            return
        self.msm.transition(Mode.NORMAL)
        self.visual_anchor = None
        self._pending_key = ""
        self.cmd_input = ""
        self.searchPattern = ""
        # move to last char 
        buf  = self.buffer
        line = buf.current_line
        if buf.cursor_col > 0 and buf.cursor_col >= len(line):
            buf.cursor_col = max(0, len(line) - 1)
        # note: helpOpen / configOpen are NOT cleared here
        # popups stay open until user explicitly closes them with q/escape from within the popup
    
    # todo - fix some of this 

    def _action_enter_insert(self):
        self.msm.transition(Mode.INSERT)

    def _action_enter_insert_after(self):
        self.msm.transition(Mode.INSERT)
        line = self.buffer.current_line
        if self.buffer.cursor_col < len(line):
            self.buffer.cursor_col += 1

    def _action_enter_insert_bol(self):
        self.msm.transition(Mode.INSERT)
        self.buffer.cursor_col = self.buffer.first_nonblank()

    def _action_enter_insert_eol(self):
        self.msm.transition(Mode.INSERT)
        self.buffer.cursor_col = len(self.buffer.current_line)

    def _action_enter_visual(self):
        self.msm.transition(Mode.VISUAL)
        self.visual_anchor = (self.buffer.cursor_row, self.buffer.cursor_col)

    def _action_enter_visual_line(self):
        self.msm.transition(Mode.VISUAL_LINE)
        self.visual_anchor = (self.buffer.cursor_row, self.buffer.cursor_col)

    def _action_enter_command(self):
        self.msm.transition(Mode.COMMAND)
        self._pending_key = ""
        self.cmd_input = ""

    def _action_enter_search(self):
        self.msm.transition(Mode.SEARCH)
        self._pending_key = ""
        self.searchPattern = ""
        self.searchBackward = False

    def _action_enter_search_back(self):
        self.msm.transition(Mode.SEARCH)
        self._pending_key = ""
        self.searchPattern = ""
        self.searchBackward = True

    def _action_execute_search(self):
        self._findMatches(self.searchPattern)
        if self.searchMatches:
            if self.searchBackward:
                self.searchIndex = len(self.searchMatches) - 1
            else:
                self.searchIndex = 0
            self._jumpToMatch(self.searchIndex)
        self._action_enter_normal()

    def _action_search_next(self):
        if not self.searchMatches:
            return
        self.searchIndex = (self.searchIndex + 1) % len(self.searchMatches)
        self._jumpToMatch(self.searchIndex)

    def _action_search_prev(self):
        if not self.searchMatches:
            return
        self.searchIndex = (self.searchIndex - 1) % len(self.searchMatches)
        self._jumpToMatch(self.searchIndex)

    def _action_open_help(self):
        self.helpOpen = True
        self.query_one(HelpMenu).open()

    def _action_close_help(self):
        self.helpOpen = False
        self.query_one(HelpMenu).close()
        self._refresh_all()

    def _findMatches(self, pattern):
        import re
        self.searchMatches = []
        if not pattern:
            return
        try:
            regex = re.compile(pattern)
        except:
            return
        for rowIdx, line in enumerate(self.buffer.lines):
            for match in regex.finditer(line):
                self.searchMatches.append((rowIdx, match.start(), match.end() - match.start()))

    def _jumpToMatch(self, matchIdx):
        if not self.searchMatches or matchIdx >= len(self.searchMatches):
            return
        row, col, length = self.searchMatches[matchIdx]
        self.buffer.move_to(row, col)
        self._refresh_all()

    # i thought about not defining methods for these but maintainbility is peak
    def _action_cursor_left(self): self.buffer.move(dcol=-1)
    def _action_cursor_right(self): self.buffer.move(dcol=1)
    def _action_cursor_up(self): self.buffer.move(drow=-1); self.buffer.clamp_col()
    def _action_cursor_down(self): self.buffer.move(drow=1);  self.buffer.clamp_col()
    def _action_line_start(self): self.buffer.cursor_col = 0
    def _action_goto_first_line(self): self.buffer.move_to(0, 0)
    def _action_goto_last_line(self): self.buffer.move_to(self.buffer.line_count - 1, 0)


    def _action_line_end(self):
        self.buffer.cursor_col = max(0, len(self.buffer.current_line) - 1)

    def _action_word_forward(self):
        buf = self.buffer
        line, col = buf.current_line, buf.cursor_col
        while col < len(line) and not line[col].isspace(): 
            col += 1
        while col < len(line) and line[col].isspace(): 
            col += 1
        if col >= len(line) and buf.cursor_row < buf.line_count - 1:
            buf.cursor_row += 1
            col = 0
        buf.cursor_col = col

    def _action_word_backward(self):
        buf = self.buffer
        line, col = buf.current_line, buf.cursor_col
        col -= 1
        while col > 0 and line[col].isspace(): 
            col -= 1
        while col > 0 and not line[col - 1].isspace(): 
            col -= 1
        buf.cursor_col = max(0, col)

    def _action_word_end(self):
        buf = self.buffer
        line, col = buf.current_line, buf.cursor_col
        col += 1
        while col < len(line) and line[col].isspace():
            col += 1
        while col < len(line) - 1 and not line[col + 1].isspace():
            col += 1
        buf.cursor_col = min(col, max(0, len(line) - 1))

    def _action_scroll_half_down(self):
        step = max(1, self.query_one(EditorWidget).size.height // 2)
        self.buffer.move(drow=step)
        self.buffer.clamp_col()

    def _action_scroll_half_up(self):
        step = max(1, self.query_one(EditorWidget).size.height // 2)
        self.buffer.move(drow=-step)
        self.buffer.clamp_col()

    # more one line functions - so peak for readability
    # if you havent gathered, i write random stuff in these comments.
    def _action_backspace(self):
        # if a snippet just expanded and user wants to undo it, revert the whole trigger
        if self._justExpanded:
            self._justExpanded = False
            self.tabStops = []
            self.tabStopIdx = 0
            for _ in range(self._revertCount):
                self.buffer.undo()
            self._revertCount = 0
            self._dismissAutocomplete()
            return
        self._justExpanded = False
        self.buffer.checkpoint()

        buf = self.buffer
        # delete matching closer if cursor is between an empty pair eg {|}
        if cfg.get("editor", "auto_pairs", True):
            col = buf.cursor_col
            line = buf.current_line
            if col > 0:
                prevCh = line[col - 1]
                nextCh = line[col:col + 1]
                if prevCh in self._PAIRS and self._PAIRS[prevCh] == nextCh:
                    # remove both chars
                    buf.lines[buf.cursor_row] = line[:col - 1] + line[col + 1:]
                    buf.cursor_col = col - 1
                    buf.modified = True
                    self._updateAutocomplete()
                    return

        # if cursor is at a tab-stop boundary, delete the whole indent chunk at once
        buf = self.buffer
        tab = _tabStr()
        tabW = len(tab)
        before = buf.current_line[:buf.cursor_col]
        if before and before == " " * len(before) and len(before) % tabW == 0 and len(before) > 0:
            # delete one full tab chunk
            for _ in range(tabW):
                buf.backspace()
        else:
            buf.backspace()

        self._updateAutocomplete()

    def _action_newline(self):
        # if autocomplete is open, enter confirms the selection
        if self.acActive and self.acItems:
            self._confirmAutocomplete()
            self._refresh_all()
            return
        import re
        self.buffer.checkpoint()
        line = self.buffer.current_line
        m = re.search(r'\\begin\{([^}]+)\}', line)
        if m:
            envName = m.group(1)
            indent = Buffer._leading_whitespace(line)
            self.buffer.newline()
            # drop cursor on blank indented line, then close env below
            contentRow = self.buffer.cursor_row
            contentCol = self.buffer.cursor_col
            self.buffer.insert(_tabStr())
            self.buffer.newline()
            self.buffer.insert(f"{indent}\\end{{{envName}}}")
            self.buffer.move_to(contentRow, contentCol + len(_tabStr()))
        else:
            self.buffer.newline()
    def _action_delete_char(self): self.buffer.checkpoint(); self.buffer.delete_char()
    def _action_undo(self): self.buffer.undo()
    def _action_redo(self): self.buffer.redo()

    def _action_open_line_below(self):
        self.msm.transition(Mode.INSERT)
        buf = self.buffer
        indent = Buffer._leading_whitespace(buf.current_line)
        buf.checkpoint()
        buf.lines.insert(buf.cursor_row + 1, indent)
        buf.cursor_row += 1
        buf.cursor_col = len(indent)
        buf.modified = True

    def _action_open_line_above(self):
        self.msm.transition(Mode.INSERT)
        buf = self.buffer
        indent = Buffer._leading_whitespace(buf.current_line)
        buf.checkpoint()
        buf.lines.insert(buf.cursor_row, indent)
        buf.cursor_col = len(indent)
        buf.modified = True

    # pairs for auto-close - opener: closer
    _PAIRS = {"{": "}", "(": ")", "[": "]", '"': '"', "`": "`"}
    # closers that should just move past instead of inserting duplicate
    _CLOSERS = set("})]\"`")

    def _insertWithAutoPairs(self, ch):
        buf = self.buffer
        if not cfg.get("editor", "auto_pairs", True):
            buf.insert(ch)
            return

        # if typing a closer and next char is already that closer, just skip past it
        nextCh = buf.current_line[buf.cursor_col:buf.cursor_col + 1]
        if ch in self._CLOSERS and nextCh == ch:
            buf.cursor_col += 1
            return

        buf.insert(ch)

        # if opener, insert the matching closer after and leave cursor between them
        if ch in self._PAIRS:
            closer = self._PAIRS[ch]
            col = buf.cursor_col
            line = buf.current_line
            buf.lines[buf.cursor_row] = line[:col] + closer + line[col:]
            # cursor stays between the pair (insert() already moved it right)

    def _doYank(self, lines, blackhole=False):
        # store lines in internal register and optionally copy to system clipboard
        # blackhole=True discards the lines entirely (no register, no clipboard)
        if blackhole:
            return
        self._yank = lines
        if _useSystemClip():
            copyToSystem("\n".join(lines))

    def _getPaste(self):
        # get lines to paste from system clipboard or internal register
        if _useSystemClip():
            text = pasteFromSystem()
            return text.split("\n") if text else []
        return self._yank

    def _action_yank_line(self):
        self._doYank([self.buffer.current_line])
        self.notify("1 line yanked")

    def _action_delete_line(self):
        self.buffer.checkpoint()
        bh = cfg.get("editor", "blackhole_delete", False)
        deleted = self.buffer.delete_line()
        self._doYank(deleted, blackhole=bh)
        n = len(deleted)
        self.notify(f"{n} line{'s' if n != 1 else ''} deleted")

    def _action_blackhole_delete_line(self):
        # "_dd - always deletes without yanking, regardless of config
        self.buffer.checkpoint()
        deleted = self.buffer.delete_line()
        self._doYank(deleted, blackhole=True)
        n = len(deleted)
        self.notify(f"{n} line{'s' if n != 1 else ''} deleted")

    def _action_paste_after(self):
        lines = self._getPaste()
        if not lines:
            return
        self.buffer.checkpoint()
        buf = self.buffer
        for i, text in enumerate(lines):
            buf.lines.insert(buf.cursor_row + 1 + i, text)
        buf.cursor_row += 1
        buf.cursor_col = buf.first_nonblank()
        buf.modified = True

    def _action_paste_before(self):
        lines = self._getPaste()
        if not lines:
            return
        self.buffer.checkpoint()
        buf = self.buffer
        for i, text in enumerate(lines):
            buf.lines.insert(buf.cursor_row + i, text)
        buf.cursor_col = buf.first_nonblank()
        buf.modified = True

    def _action_indent(self):
        self.buffer.checkpoint()
        buf = self.buffer
        tab = _tabStr()
        buf.lines[buf.cursor_row] = tab + buf.current_line
        buf.cursor_col = min(buf.cursor_col + len(tab), len(buf.current_line))
        buf.modified = True

    def _action_dedent(self):
        self.buffer.checkpoint()
        buf = self.buffer
        line = buf.current_line
        removed = len(line) - len(line.lstrip(" "))
        removed = min(removed, 4)
        buf.lines[buf.cursor_row] = line[removed:]
        buf.cursor_col = max(0, buf.cursor_col - removed)
        buf.modified = True

    def _action_delete_word_before(self):
        self.buffer.checkpoint()
        buf = self.buffer
        line, col = buf.current_line, buf.cursor_col
        while col > 0 and line[col - 1].isspace(): col -= 1
        while col > 0 and not line[col - 1].isspace(): col -= 1
        buf.lines[buf.cursor_row] = line[:col] + line[buf.cursor_col:]
        buf.cursor_col = col
        buf.modified = True

    def _action_delete_to_line_start(self):
        self.buffer.checkpoint()
        buf = self.buffer
        buf.lines[buf.cursor_row] = buf.current_line[buf.cursor_col:]
        buf.cursor_col = 0
        buf.modified = True

    def _action_execute_command(self):
        cmd = self.cmd_input.strip()
        self._action_enter_normal()   # resets mode + clears cmd_input

        if cmd == "w":
            self._cmd_write()
        elif cmd == "q":
            self._cmd_quit()
        elif cmd in ("wq", "x"):
            self._cmd_write()
            self.exit()
        elif cmd == "q!":
            self.exit()
        elif cmd in ("help", "h"):
            self._action_open_help()
        elif cmd in ("snippets", "snips"):
            # open help menu straight to the snippets tab
            self.helpOpen = True
            menu = self.query_one(HelpMenu)
            menu.open()
            # advance to snippets tab (index 1)
            menu.nextTab()
        elif cmd.startswith("e "):
            path = cmd[2:].strip()
            if path:
                self.buffer.load(path)
                self._refresh_all()
        elif cmd.startswith("w "):
            path = cmd[2:].strip()
            if path:
                self.buffer.save(path)
        elif cmd in ("config show", "config"):
            self._cmd_configShow()
        elif cmd in ("config set", "config get"):
            # bare commands without args 
            # TODO - make this better
            self.notify(f":{cmd} <section.key> <value>" if cmd == "config set" else f":{cmd} <section.key>", severity="warning")
        elif cmd.startswith("config set"):
            self._cmd_configSet(cmd[len("config set"):].strip())
        elif cmd.startswith("config get"):
            self._cmd_configGet(cmd[len("config get"):].strip())
        elif cmd in ("build", "compile", "b"):
            self._cmd_build()
        elif cmd.startswith("build ") or cmd.startswith("compile "):
            engine = cmd.split(None, 1)[1].strip()
            self._cmd_build(engine=engine)
        elif cmd == "clean":
            self._cmd_clean()
        elif cmd in ("buildlog", "buildpanel"):
            self._cmd_buildlog()
        elif cmd in ("buildstop", "killbuild"):
            self._cmd_buildstop()
        elif cmd in ("engines", "compilers"):
            self._cmd_listEngines()
        else:
            self.notify(f"unknown command: {cmd}", severity="warning")

    def _cmd_configShow(self):
        self.configOpen = True
        self.query_one(ConfigPanel).open()

    def _cmd_configSet(self, args):
        # :config set section.key value  OR  :config set key value (auto-detects section)
        parts = args.split(None, 1)
        if len(parts) != 2:
            self.notify(":config set <section.key> <value>", severity="warning")
            return
        dotKey, rawVal = parts
        section, key = _resolveConfigKey(dotKey)
        if section is None:
            self.notify(f"config: unknown key '{dotKey}'", severity="warning")
            return
        value = _coerceValue(rawVal)
        cfg.set(section, key, value)
        self.notify(f"config: {section}.{key} = {value}")

    def _cmd_configGet(self, dotKey):
        # :config get section.key  OR  :config get key
        if not dotKey:
            self.notify(":config get <section.key>", severity="warning")
            return
        section, key = _resolveConfigKey(dotKey)
        if section is None:
            self.notify(f"config: unknown key '{dotKey}'", severity="warning")
            return
        val = cfg.get(section, key)
        if val is None:
            self.notify(f"config: {section}.{key} not set", severity="warning")
        else:
            self.notify(f"{section}.{key} = {val}")

    def _cmd_write(self):
        if not self.buffer.path:
            self.notify("no file name - use :w <filename>", severity="warning")
            return
        self.buffer.save()
        self.notify(f"saved {self.buffer.path}")
        if cfg.get("editor", "autocompile", False):
            self._cmd_build()

    def _cmd_build(self, engine=None):
        if not self.buffer.path:
            self.notify("save file first before building", severity="warning")
            return

        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()

        self.buffer.save()

        engine    = engine or cfg.get("editor", "compiler", "latexmk")
        auxDir    = cfg.get("editor", "aux_dir", ".aux")
        customCmd = cfg.get("editor", "custom_compile_cmd", "") or None

        # custom_compile_cmd takes priority - no need to change compiler setting
        if not customCmd and engine not in _compiler.PRESETS:
            self.notify(f"unknown engine '{engine}' - use :engines to list options", severity="warning")
            return

        panel = self.query_one(BuildPanel)
        panel.reset(engine, self.buffer.path)
        panel.display = True
        self.buildOpen = True

        async def _run():
            def onLine(line, isErr):
                panel.appendLine(line, isErr)

            try:
                rc, _ = await _compiler.compile(
                    self.buffer.path,
                    engine=engine,
                    auxConfig=auxDir,
                    customCmd=customCmd,
                    onLine=onLine,
                )
                panel.setDone(rc)
                if rc == 0:
                    self.notify(f"build succeeded ({engine})", timeout=3)
                else:
                    self.notify(f"build failed (exit {rc})", severity="error", timeout=5)
            except asyncio.CancelledError:
                panel.appendLine("build cancelled", True)
                panel.setDone(1)
            except Exception as e:
                panel.appendLine(f"error: {e}", True)
                panel.setDone(1)

        import asyncio
        self._buildTask = asyncio.create_task(_run())

    def _cmd_clean(self):
        if not self.buffer.path:
            self.notify("no file open", severity="warning")
            return
        auxDir = cfg.get("editor", "aux_dir", ".aux")
        try:
            count = _compiler.cleanAuxDir(self.buffer.path, auxDir)
            self.notify(f"cleaned {count} file{'s' if count != 1 else ''} from aux dir")
        except Exception as e:
            self.notify(f"clean failed: {e}", severity="error")

    def _cmd_buildlog(self):
        panel = self.query_one(BuildPanel)
        if not panel._lines:
            self.notify("no build output yet - run :build first", severity="warning")
            return
        panel.display = True
        self.buildOpen = True

    def _cmd_buildstop(self):
        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("build cancelled")
        else:
            self.notify("no build running", severity="warning")

    def _cmd_listEngines(self):
        panel = self.query_one(BuildPanel)
        panel.reset("engines", "available engines")
        for name, desc in _compiler.ENGINE_DESCRIPTIONS.items():
            panel.appendLine(f"  {name:<14} {desc}", autoScroll=False)
        current = cfg.get("editor", "compiler", "latexmk")
        customCmd = cfg.get("editor", "custom_compile_cmd", "")
        panel.appendLine("", autoScroll=False)
        if customCmd:
            panel.appendLine(f"  custom_compile_cmd is set - will be used instead of engine", autoScroll=False)
            panel.appendLine(f"  cmd: {customCmd}", autoScroll=False)
        else:
            panel.appendLine(f"  current engine: {current}  (editor.compiler)", autoScroll=False)
            panel.appendLine(f"  to use custom cmd: set editor.custom_compile_cmd", autoScroll=False)
        panel._scroll = 0
        panel.setDone(0)
        panel.display = True
        self.buildOpen = True




    def _cmd_quit(self):
        if self.buffer.modified:
            self.notify("unsaved changes - use :q! to force quit", severity="warning")
            return
        self.exit()
    
    def _action_insert_tab(self):
        # autocomplete popup is open - tab cycles down through items
        if self.acActive and self.acItems:
            self.acIndex = (self.acIndex + 1) % len(self.acItems)
            self._refreshAutocomplete()
            return

        buf = self.buffer
        textBefore = buf.current_line[:buf.cursor_col]

        # new snippet trigger takes priority over stale tab stops from a previous snippet
        trigger, snippet = self.snippets.findTabTrigger(textBefore)
        if trigger and snippet:
            self.buffer.checkpoint()
            self.tabStops = self.snippets.expandInBuffer(trigger, snippet.get("body", ""), buf)
            self.tabStopIdx = 0
            self._justExpanded = True
            self._revertCount = 1
            if self.tabStops:
                row, col = self.tabStops[0]
                buf.move_to(row, col)
                self._lastTabRow, self._lastTabCol = row, col
                self.tabStopIdx = 1
            return

        # jump to next tab stop - adjust positions for any chars typed at the previous stop
        if self.tabStops and self.tabStopIdx < len(self.tabStops):
            self._justExpanded = False
            self._revertCount = 0

            # chars typed since we landed on the last stop (same row only)
            delta = 0
            if buf.cursor_row == self._lastTabRow:
                delta = buf.cursor_col - self._lastTabCol

            # shift all remaining stops on the same row by that delta
            if delta != 0:
                self.tabStops = [
                    (r, c + delta if r == self._lastTabRow else c)
                    for r, c in self.tabStops
                ]

            row, col = self.tabStops[self.tabStopIdx]
            self.tabStopIdx += 1
            if self.tabStopIdx >= len(self.tabStops):
                self.tabStops = []
                self.tabStopIdx = 0
            self._lastTabRow, self._lastTabCol = row, col
            self.buffer.move_to(row, col)
            return

        # otherwise indent if line is blank before cursor
        self._justExpanded = False
        before = buf.current_line[:buf.cursor_col]
        if not before.strip():
            buf.checkpoint()
            buf.insert(_tabStr())

    # placeholders for later
    def _action_smart_tab(self): pass
    def _action_clear_tab_stops(self):
        # shift+tab - dismiss autocomplete or just clear tab stops
        self.tabStops = []
        self.tabStopIdx = 0
        self._dismissAutocomplete()
    def _action_accept_autocomplete(self):
        # ctrl+space - confirm selected completion
        self._confirmAutocomplete()

    # replace char mode
    def _action_replace_char(self):
        self._awaiting_replace = True


    def _selection_bounds(self): 
        if self.visual_anchor is None:
            return None
        a_row, a_col = self.visual_anchor
        c_row, c_col = self.buffer.cursor_row, self.buffer.cursor_col
        if (a_row, a_col) <= (c_row, c_col):
            return a_row, a_col, c_row, c_col
        return c_row, c_col, a_row, a_col # ensures r0,c0 is top-left and r1,c1 is bottom-right of selection 

    def _action_yank_selection(self):
        buf = self.buffer
        if self.msm.mode is Mode.VISUAL_LINE:
            if self.visual_anchor is None:
                return
            r0 = min(self.visual_anchor[0], buf.cursor_row)
            r1 = max(self.visual_anchor[0], buf.cursor_row)
            yanked = list(buf.lines[r0 : r1 + 1])
        else:
            bounds = self._selection_bounds()
            if bounds is None:
                return
            r0, c0, r1, c1 = bounds
            if r0 == r1:
                yanked = [buf.lines[r0][c0 : c1 + 1]]
            else:
                yanked = (
                    [buf.lines[r0][c0:]]
                    + list(buf.lines[r0 + 1 : r1])
                    + [buf.lines[r1][: c1 + 1]]
                )
        # hello random person reading this code
        self._doYank(yanked)
        self._action_enter_normal()
        n = len(self._yank)
        self.notify(f"{n} line{'s' if n != 1 else ''} yanked")

    def _action_delete_selection(self):
        buf = self.buffer
        buf.checkpoint()
        # i need to seperate this across diff files, using vim to edit 1k+ lines is cancer :(, most of the code is just the same but for diff selection modes, so forgive the repetition please ...
        if self.msm.mode is Mode.VISUAL_LINE:
            if self.visual_anchor is None:
                return
            r0 = min(self.visual_anchor[0], buf.cursor_row)
            r1 = max(self.visual_anchor[0], buf.cursor_row)
            bh = cfg.get("editor", "blackhole_delete", False)
            self._doYank(list(buf.lines[r0 : r1 + 1]), blackhole=bh)
            del buf.lines[r0 : r1 + 1]
            if not buf.lines:
                buf.lines = [""]
            buf.cursor_row = min(r0, buf.line_count - 1)
            buf.cursor_col = 0
        else:
            bounds = self._selection_bounds()
            if bounds is None:
                return
            r0, c0, r1, c1 = bounds
            bh = cfg.get("editor", "blackhole_delete", False)
            if r0 == r1:
                line = buf.lines[r0]
                self._doYank([line[c0 : c1 + 1]], blackhole=bh)
                buf.lines[r0] = line[:c0] + line[c1 + 1 :]
                buf.cursor_col = c0
            else:
                self._doYank(
                    [buf.lines[r0][c0:]]
                    + list(buf.lines[r0 + 1 : r1])
                    + [buf.lines[r1][: c1 + 1]],
                    blackhole=bh,
                )
                buf.lines[r0] = buf.lines[r0][:c0] + buf.lines[r1][c1 + 1 :]
                del buf.lines[r0 + 1 : r1 + 1]
                buf.cursor_row = r0
                buf.cursor_col = c0
        buf.modified = True
        self._action_enter_normal()


