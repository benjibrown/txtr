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
        self._commandSourceMode = None
        self._pending_key = ""
        self.cmd_input = ""
        self.searchPattern = ""
        buf  = self.buffer
        line = buf.current_line
        if buf.cursor_col > 0 and buf.cursor_col >= len(line):
            buf.cursor_col = max(0, len(line) - 1)

    def _action_enter_insert(self):
        self.msm.transition(Mode.INSERT)
    
    # so many helpers :(
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
        self._commandSourceMode = self.msm.mode
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

    # son im crine 
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
        if hasattr(self, "_closeOverlayPanels"):
            self._closeOverlayPanels(except_name="help")
        self.helpOpen = True
        self.query_one("HelpMenu").open()

    def _action_close_help(self):
        self.helpOpen = False
        self.query_one("HelpMenu").close()
        self._refresh_all()

    # cursor movement

    def _action_cursor_left(self):
        buf = self.buffer
        if buf.cursor_col == 0 and buf.cursor_row > 0:
            prev_row = buf.cursor_row - 1
            prev_line = buf.lines[prev_row]
            target = len(prev_line) if self.msm.is_insert() else max(0, len(prev_line) - 1)
            buf.move_to(prev_row, target)
            return
        buf.move(dcol=-1)

    def _action_cursor_right(self): self.buffer.move(dcol=1)

    def _action_cursor_up(self):
        if self.acActive and self.acItems and self.msm.is_insert():
            self.acIndex = (self.acIndex - 1) % len(self.acItems)
            self._refreshAutocomplete()
            return
        self.buffer.move(drow=-1)
        self.buffer.clamp_col()

    def _action_cursor_down(self):
        if self.acActive and self.acItems and self.msm.is_insert():
            self.acIndex = (self.acIndex + 1) % len(self.acItems)
            self._refreshAutocomplete()
            return
        self.buffer.move(drow=1)
        self.buffer.clamp_col()

    def _action_jump_100_down(self):
        self.buffer.move(drow=100)
        self.buffer.clamp_col()

    def _action_jump_100_up(self):
        self.buffer.move(drow=-100)
        self.buffer.clamp_col()

    def _action_next_buffer(self):
        self._nextBuffer()

    def _action_prev_buffer(self):
        self._prevBuffer()

    def _action_line_start(self):   self.buffer.cursor_col = 0
    def _action_goto_first_line(self): self.buffer.move_to(0, 0)
    def _action_goto_last_line(self):  self.buffer.move_to(self.buffer.line_count - 1, 0)

    def _action_line_end(self):
        self.buffer.cursor_col = max(0, len(self.buffer.current_line) - 1)

    def _wordKind(self, ch):
        # vim-ish word classes - words, spaces, and the punctuation jungle
        if ch.isspace():
            return "space"
        if ch.isalnum() or ch == "_":
            return "word"
        return "punct"

    def _currentCharPos(self):
        # this just gives us a sane scan position even if the cursor is at line end
        row = self.buffer.cursor_row
        line = self.buffer.lines[row]
        if not line:
            return row, 0
        col = min(self.buffer.cursor_col, len(line) - 1)
        return row, col

    def _nextCharPos(self, row, col):
        lines = self.buffer.lines
        if row >= len(lines):
            return None
        line = lines[row]
        if col + 1 < len(line):
            return row, col + 1
        row += 1
        while row < len(lines):
            if lines[row]:
                return row, 0
            row += 1
        return None

    def _prevCharPos(self, row, col):
        lines = self.buffer.lines
        if row < 0:
            return None
        if row < len(lines) and lines[row] and col > 0:
            return row, col - 1
        row -= 1
        while row >= 0:
            if lines[row]:
                return row, len(lines[row]) - 1
            row -= 1
        return None

    def _nextWordStart(self, row, col):
        # lowercase vim words basically treat punctuation as its own lil chunk
        lines = self.buffer.lines
        line = lines[row]
        if not line:
            pos = self._nextCharPos(row, -1)
            while pos:
                prow, pcol = pos
                if not lines[prow][pcol].isspace():
                    return pos
                pos = self._nextCharPos(prow, pcol)
            return None

        ch = line[col]
        pos = (row, col)
        if ch.isspace():
            while pos:
                prow, pcol = pos
                if not lines[prow][pcol].isspace():
                    return pos
                pos = self._nextCharPos(prow, pcol)
            return None

        kind = self._wordKind(ch)
        pos = self._nextCharPos(row, col)
        while pos:
            prow, pcol = pos
            nxt = lines[prow][pcol]
            if nxt.isspace():
                while pos:
                    prow, pcol = pos
                    if not lines[prow][pcol].isspace():
                        return pos
                    pos = self._nextCharPos(prow, pcol)
                return None
            if self._wordKind(nxt) != kind:
                return pos
            pos = self._nextCharPos(prow, pcol)
        return None

    def _wordStartFrom(self, row, col):
        lines = self.buffer.lines
        kind = self._wordKind(lines[row][col])
        pos = (row, col)
        prev = self._prevCharPos(row, col)
        while prev:
            prow, pcol = prev
            ch = lines[prow][pcol]
            if ch.isspace() or self._wordKind(ch) != kind:
                break
            pos = prev
            prev = self._prevCharPos(prow, pcol)
        return pos
    # get us to prev word start (or current if in middle)
    def _prevWordStart(self, row, col):
        lines = self.buffer.lines
        line = lines[row]
        if not line:
            pos = self._prevCharPos(row, col)
            while pos:
                prow, pcol = pos
                if not lines[prow][pcol].isspace():
                    return self._wordStartFrom(prow, pcol)
                pos = self._prevCharPos(prow, pcol)
            return None

        ch = line[col]
        if ch.isspace():
            pos = (row, col)
            while pos and lines[pos[0]][pos[1]].isspace():
                pos = self._prevCharPos(pos[0], pos[1])
            if not pos:
                return None
            return self._wordStartFrom(pos[0], pos[1])

        prev = self._prevCharPos(row, col)
        if prev:
            pch = lines[prev[0]][prev[1]]
            if not pch.isspace() and self._wordKind(pch) == self._wordKind(ch):
                return self._wordStartFrom(row, col)

        pos = prev
        while pos and lines[pos[0]][pos[1]].isspace():
            pos = self._prevCharPos(pos[0], pos[1])
        if not pos:
            return None
        return self._wordStartFrom(pos[0], pos[1]) 
        # the algos are all pretty similiar but edge cases i hate so much


    # this is basically the same as _wordStartFrom but in the other direction   
    def _wordEndFrom(self, row, col):

        lines = self.buffer.lines
        kind = self._wordKind(lines[row][col])
        pos = (row, col)
        nxt = self._nextCharPos(row, col)
        while nxt:
            nrow, ncol = nxt
            ch = lines[nrow][ncol]
            if ch.isspace() or self._wordKind(ch) != kind:
                break
            pos = nxt
            nxt = self._nextCharPos(nrow, ncol)
        return pos
    # get us to end of current word (i hope)
    def _nextWordEnd(self, row, col):
        lines = self.buffer.lines
        line = lines[row]
        if not line:
            pos = self._nextCharPos(row, -1)
            while pos:
                prow, pcol = pos
                if not lines[prow][pcol].isspace():
                    return self._wordEndFrom(prow, pcol)
                pos = self._nextCharPos(prow, pcol)
            return None

        ch = line[col]
        if ch.isspace():
            pos = (row, col)
            while pos and lines[pos[0]][pos[1]].isspace():
                pos = self._nextCharPos(pos[0], pos[1])
            if not pos:
                return None
            return self._wordEndFrom(pos[0], pos[1])
        return self._wordEndFrom(row, col)

    def _action_word_forward(self):
        row, col = self._currentCharPos()
        target = self._nextWordStart(row, col)
        if target:
            self.buffer.move_to(*target)

    def _action_word_backward(self):
        row, col = self._currentCharPos()
        target = self._prevWordStart(row, col)
        if target:
            self.buffer.move_to(*target)

    def _action_word_end(self):
        row, col = self._currentCharPos()
        target = self._nextWordEnd(row, col)
        if target:
            self.buffer.move_to(*target)

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

    def _expandSnippetTrigger(self, trigger, snippet):
        # this just does the shared snippet expansion bit so it isnt copy pasted everywhere
        buf = self.buffer
        buf.checkpoint()
        self.tabStops = self.snippets.expandInBuffer(trigger, snippet.get("body", ""), buf)
        self.tabStopIdx = 0
        self._justExpanded = True
        self._revertCount = 1
        if self.tabStops:
            row, col, length = self.tabStops[0]
            buf.move_to(row, col)
            self._lastTabRow, self._lastTabCol, self._lastTabLength = row, col, length
            self.tabStopIdx = 1

    def _action_insert_tab(self):
        from texitor.ui.app import _tabStr
        buf = self.buffer
        textBefore = buf.current_line[:buf.cursor_col]

        trigger, snippet = self.snippets.findTabTrigger(textBefore)
        if trigger and snippet:
            self._expandSnippetTrigger(trigger, snippet)
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

    def _selectedText(self):
        from texitor.core.modes import Mode

        buf = self.buffer
        if self.msm.mode is Mode.VISUAL_LINE:
            if self.visual_anchor is None:
                return ""
            r0 = min(self.visual_anchor[0], buf.cursor_row)
            r1 = max(self.visual_anchor[0], buf.cursor_row)
            return "\n".join(buf.lines[r0 : r1 + 1])

        bounds = self._selection_bounds()
        if bounds is None:
            return ""
        r0, c0, r1, c1 = bounds
        if r0 == r1:
            return buf.lines[r0][c0 : c1 + 1]
        parts = [buf.lines[r0][c0:]] + list(buf.lines[r0 + 1 : r1]) + [buf.lines[r1][: c1 + 1]]
        return "\n".join(parts)

    def _replaceSelectionText(self, text):
        from texitor.core.modes import Mode

        buf = self.buffer
        bounds = self._selection_bounds()
        if self.msm.mode is Mode.VISUAL_LINE:
            if self.visual_anchor is None:
                return False
            r0 = min(self.visual_anchor[0], buf.cursor_row)
            r1 = max(self.visual_anchor[0], buf.cursor_row)
            buf.checkpoint()
            buf.lines[r0 : r1 + 1] = text.split("\n") or [""]
            buf.cursor_row = r0 + len(text.split("\n")) - 1
            buf.cursor_col = len((text.split("\n") or [""])[-1])
            buf.modified = True
            self._action_enter_normal()
            return True

        if bounds is None:
            return False
        r0, c0, r1, c1 = bounds
        buf.checkpoint()
        if r0 == r1:
            line = buf.lines[r0]
            buf.lines[r0] = line[:c0] + text + line[c1 + 1:]
            inserted = text.split("\n")
            if len(inserted) == 1:
                buf.cursor_row = r0
                buf.cursor_col = c0 + len(inserted[0])
            else:
                tail = line[c1 + 1:]
                merged = (line[:c0] + text + tail).split("\n")
                buf.lines[r0 : r0 + 1] = merged
                buf.cursor_row = r0 + len(merged) - 1
                buf.cursor_col = len(merged[-1]) - len(tail)
        else:
            start = buf.lines[r0][:c0]
            end = buf.lines[r1][c1 + 1:]
            merged = (start + text + end).split("\n")
            buf.lines[r0 : r1 + 1] = merged
            buf.cursor_row = r0 + len(merged) - 1
            buf.cursor_col = len(merged[-1]) - len(end)
        buf.modified = True
        self._action_enter_normal()
        return True

    def _action_system_copy(self):
        from texitor.core.clipboard import copyToSystem
        from texitor.core.modes import Mode

        if self.msm.mode in (Mode.VISUAL, Mode.VISUAL_LINE) and self.visual_anchor is not None:
            text = self._selectedText()
            if not text:
                return
            copyToSystem(text)
            self.notify("selection copied")
            return
        if self.msm.is_command():
            copyToSystem(self.cmd_input)
            self.notify("command copied")
            return
        if self.msm.is_search():
            copyToSystem(self.searchPattern)
            self.notify("search copied")
            return
        copyToSystem(self.buffer.current_line)
        self.notify("line copied")

    def _action_system_paste(self):
        from texitor.core.clipboard import pasteFromSystem
        from texitor.core.modes import Mode

        text = pasteFromSystem()
        if not text:
            return

        if self.msm.is_command():
            self.cmd_input += text
            return
        if self.msm.is_search():
            self.searchPattern += text
            return
        if self.msm.mode in (Mode.VISUAL, Mode.VISUAL_LINE) and self.visual_anchor is not None:
            self._replaceSelectionText(text)
            self._dismissAutocomplete()
            self._updateAutocomplete()
            return

        self.buffer.checkpoint()
        self.buffer.insert(text)
        self._dismissAutocomplete()
        self._updateAutocomplete()

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
