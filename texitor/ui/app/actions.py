# actions mixin - all _action_* methods for navigation, editing and mode transitions
# mixed into TxtrApp via ActionsMixin

from __future__ import annotations
import re

from texitor.core.buffer import Buffer
from texitor.core.modes import Mode


class ActionsMixin:

    # mode transitions

    def _action_enter_normal(self):
        if self.acActive:
            self._dismissAutocomplete()
            self._refresh_all()
            return
        self.msm.transition(Mode.NORMAL)
        self.visual_anchor = None
        self._pending_key = ""
        self.cmd_input = ""
        self.searchPattern = ""
        buf  = self.buffer
        line = buf.current_line
        if buf.cursor_col > 0 and buf.cursor_col >= len(line):
            buf.cursor_col = max(0, len(line) - 1)

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

    # search

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

    def _findMatches(self, pattern):
        self.searchMatches = []
        if not pattern:
            return
        try:
            regex = re.compile(pattern)
        except Exception:
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

    # help menu

    def _action_open_help(self):
        self.helpOpen = True
        self.query_one("HelpMenu").open()

    def _action_close_help(self):
        self.helpOpen = False
        self.query_one("HelpMenu").close()
        self._refresh_all()

    # cursor movement

    def _action_cursor_left(self):  self.buffer.move(dcol=-1)
    def _action_cursor_right(self): self.buffer.move(dcol=1)
    def _action_cursor_up(self):    self.buffer.move(drow=-1); self.buffer.clamp_col()
    def _action_cursor_down(self):  self.buffer.move(drow=1);  self.buffer.clamp_col()
    def _action_line_start(self):   self.buffer.cursor_col = 0
    def _action_goto_first_line(self): self.buffer.move_to(0, 0)
    def _action_goto_last_line(self):  self.buffer.move_to(self.buffer.line_count - 1, 0)

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
        from texitor.ui.editor import EditorWidget
        step = max(1, self.query_one(EditorWidget).size.height // 2)
        self.buffer.move(drow=step)
        self.buffer.clamp_col()

    def _action_scroll_half_up(self):
        from texitor.ui.editor import EditorWidget
        step = max(1, self.query_one(EditorWidget).size.height // 2)
        self.buffer.move(drow=-step)
        self.buffer.clamp_col()

    # editing

    def _action_backspace(self):
        from texitor.core.config import config as cfg
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
        if cfg.get("editor", "auto_pairs", True):
            col = buf.cursor_col
            line = buf.current_line
            if col > 0:
                prevCh = line[col - 1]
                nextCh = line[col:col + 1]
                if prevCh in self._PAIRS and self._PAIRS[prevCh] == nextCh:
                    buf.lines[buf.cursor_row] = line[:col - 1] + line[col + 1:]
                    buf.cursor_col = col - 1
                    buf.modified = True
                    self._updateAutocomplete()
                    return

        from texitor.ui.app import _tabStr
        tab = _tabStr()
        tabW = len(tab)
        before = buf.current_line[:buf.cursor_col]
        if before and before == " " * len(before) and len(before) % tabW == 0 and len(before) > 0:
            for _ in range(tabW):
                buf.backspace()
        else:
            buf.backspace()
        self._updateAutocomplete()

    def _action_newline(self):
        if self.acActive and self.acItems:
            self._confirmAutocomplete()
            self._refresh_all()
            return
        from texitor.ui.app import _tabStr
        self.buffer.checkpoint()
        line = self.buffer.current_line
        m = re.search(r'\\begin\{([^}]+)\}', line)
        if m:
            envName = m.group(1)
            indent = Buffer._leading_whitespace(line)
            self.buffer.newline()
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
    _PAIRS   = {"{": "}", "(": ")", "[": "]", '"': '"', "`": "`"}
    _CLOSERS = set("})]\"`")

    def _insertWithAutoPairs(self, ch):
        from texitor.core.config import config as cfg
        buf = self.buffer
        if not cfg.get("editor", "auto_pairs", True):
            buf.insert(ch)
            return
        nextCh = buf.current_line[buf.cursor_col:buf.cursor_col + 1]
        if ch in self._CLOSERS and nextCh == ch:
            buf.cursor_col += 1
            return
        buf.insert(ch)
        if ch in self._PAIRS:
            closer = self._PAIRS[ch]
            col = buf.cursor_col
            line = buf.current_line
            buf.lines[buf.cursor_row] = line[:col] + closer + line[col:]

    # yank / paste / delete

    def _doYank(self, lines, blackhole=False):
        from texitor.ui.app import _useSystemClip
        from texitor.core.clipboard import copyToSystem
        if blackhole:
            return
        self._yank = lines
        if _useSystemClip():
            copyToSystem("\n".join(lines))

    def _getPaste(self):
        from texitor.ui.app import _useSystemClip
        from texitor.core.clipboard import pasteFromSystem
        if _useSystemClip():
            text = pasteFromSystem()
            return text.split("\n") if text else []
        return self._yank

    def _action_yank_line(self):
        self._doYank([self.buffer.current_line])
        self.notify("1 line yanked")

    def _action_delete_line(self):
        from texitor.core.config import config as cfg
        self.buffer.checkpoint()
        bh = cfg.get("editor", "blackhole_delete", False)
        deleted = self.buffer.delete_line()
        self._doYank(deleted, blackhole=bh)
        n = len(deleted)
        self.notify(f"{n} line{'s' if n != 1 else ''} deleted")

    def _action_blackhole_delete_line(self):
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
        from texitor.ui.app import _tabStr
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

    # replace char

    def _action_replace_char(self):
        self._awaiting_replace = True

    # tab stops / snippets

    def _action_insert_tab(self):
        if self.acActive and self.acItems:
            self.acIndex = (self.acIndex + 1) % len(self.acItems)
            self._refreshAutocomplete()
            return

        from texitor.ui.app import _tabStr
        buf = self.buffer
        textBefore = buf.current_line[:buf.cursor_col]

        trigger, snippet = self.snippets.findTabTrigger(textBefore)
        if trigger and snippet:
            self.buffer.checkpoint()
            self.tabStops = self.snippets.expandInBuffer(trigger, snippet.get("body", ""), buf)
            self.tabStopIdx = 0
            self._justExpanded = True
            self._revertCount = 1
            if self.tabStops:
                row, col, length = self.tabStops[0]
                buf.move_to(row, col)
                self._lastTabRow, self._lastTabCol, self._lastTabLength = row, col, length
                self.tabStopIdx = 1
            return

        if self.tabStops and self.tabStopIdx < len(self.tabStops):
            self._justExpanded = False
            self._revertCount = 0
            delta = 0
            if buf.cursor_row == self._lastTabRow:
                baseline = self._lastTabCol + self._lastTabLength
                delta = buf.cursor_col - baseline
            if delta != 0:
                self.tabStops = [
                    (r, c + delta if r == self._lastTabRow else c, l)
                    for r, c, l in self.tabStops
                ]
            row, col, length = self.tabStops[self.tabStopIdx]
            self.tabStopIdx += 1
            if self.tabStopIdx >= len(self.tabStops):
                self.tabStops = []
                self.tabStopIdx = 0
            self._lastTabRow, self._lastTabCol, self._lastTabLength = row, col, length
            self.buffer.move_to(row, col)
            return

        self._justExpanded = False
        before = buf.current_line[:buf.cursor_col]
        if not before.strip():
            buf.checkpoint()
            buf.insert(_tabStr())

    def _action_smart_tab(self): pass

    def _action_clear_tab_stops(self):
        self.tabStops = []
        self.tabStopIdx = 0
        self._dismissAutocomplete()

    def _action_accept_autocomplete(self):
        self._confirmAutocomplete()

    # visual selection helpers

    def _selection_bounds(self):
        if self.visual_anchor is None:
            return None
        a_row, a_col = self.visual_anchor
        c_row, c_col = self.buffer.cursor_row, self.buffer.cursor_col
        if (a_row, a_col) <= (c_row, c_col):
            return a_row, a_col, c_row, c_col
        return c_row, c_col, a_row, a_col

    def _action_yank_selection(self):
        from texitor.core.modes import Mode
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
        self._doYank(yanked)
        self._action_enter_normal()
        n = len(self._yank)
        self.notify(f"{n} line{'s' if n != 1 else ''} yanked")

    def _action_delete_selection(self):
        from texitor.core.config import config as cfg
        from texitor.core.modes import Mode
        buf = self.buffer
        buf.checkpoint()
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
                buf.lines[r0] = line[:c0] + line[c1 + 1:]
                buf.cursor_col = c0
            else:
                self._doYank(
                    [buf.lines[r0][c0:]]
                    + list(buf.lines[r0 + 1 : r1])
                    + [buf.lines[r1][: c1 + 1]],
                    blackhole=bh,
                )
                buf.lines[r0] = buf.lines[r0][:c0] + buf.lines[r1][c1 + 1:]
                del buf.lines[r0 + 1 : r1 + 1]
                buf.cursor_row = r0
                buf.cursor_col = c0
        buf.modified = True
        self._action_enter_normal()
