
# main app.
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.events import Key

from texitor.core.buffer import Buffer
from texitor.core.keybinds import KeybindRegistry
from texitor.core.modes import Mode, ModeStateMachine
# placeholder imports
from texitor.ui.editor import EditorWidget
from texitor.ui.statusbar import StatusBar



class TxtrApp(App):
    # main app class - the big boy class that holds all of my janky code together...

    TITLE = "txtr" # aka texitor but who wants to type allat
    ENABLE_COMMAND_PALETTE = False
    CSS = "Screen { }"

    def __init__(self, filename=None):
        super().__init__()
        self.buffer = Buffer()
        self.msm = ModeStateMachine()
        self.keybinds = KeybindRegistry()
        self._yank = []
        self.visual_anchor = None 
        self._pending_key = ""   # accumulates multi-key sequences e.g. "g", "d"
        self._awaiting_replace = False  # true after r — next key replaces char

        if filename:
            self.buffer.load(filename)

    # layout of app (editor + bar)
    def compose(self):
        yield EditorWidget(self.buffer, self.msm, self)
        yield StatusBar(self.buffer, self.msm)

    # key handling
    def on_key(self, event: Key):
        event.stop()
        event.prevent_default()

        key = event.key

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
        mode = self.msm.mode
        candidate = (self._pending_key + " " + key).strip()

        action = self.keybinds.get(mode, candidate)
        if action:
            self._pending_key = ""
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler()
            self._refresh_all()
            return

        # wait for more keys if needed
        if self._is_prefix(mode, candidate):
            self._pending_key = candidate
            return

        # if not then just try the single key
        self._pending_key = ""
        action = self.keybinds.get(mode, key)
        if action:
            handler = getattr(self, f"_action_{action}", None)
            if handler:
                handler()
            self._refresh_all()
            return

        # insert mode - any chars printable 
        if self.msm.is_insert() and event.character and event.character.isprintable():
            self.buffer.checkpoint()
            self.buffer.insert(event.character)
            self._refresh_all()

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

    # mode trans 
    def _action_enter_normal(self):
        self.msm.transition(Mode.NORMAL)
        self.visual_anchor = None
        # move to last char 
        buf  = self.buffer
        line = buf.current_line
        if buf.cursor_col > 0 and buf.cursor_col >= len(line):
            buf.cursor_col = max(0, len(line) - 1)
    
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
    def _action_backspace(self): self.buffer.checkpoint(); self.buffer.backspace()
    def _action_newline(self): self.buffer.checkpoint(); self.buffer.newline()
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

    def _action_yank_line(self):
        self._yank = [self.buffer.current_line]

    def _action_delete_line(self):
        self.buffer.checkpoint()
        self._yank = self.buffer.delete_line()

    def _action_paste_after(self):
        if not self._yank:
            return
        self.buffer.checkpoint()
        buf = self.buffer
        for i, text in enumerate(self._yank):
            buf.lines.insert(buf.cursor_row + 1 + i, text)
        buf.cursor_row += 1
        buf.cursor_col = buf.first_nonblank()
        buf.modified = True

    def _action_paste_before(self):
        if not self._yank:
            return
        self.buffer.checkpoint()
        buf = self.buffer
        for i, text in enumerate(self._yank):
            buf.lines.insert(buf.cursor_row + i, text)
        buf.cursor_col = buf.first_nonblank()
        buf.modified = True

    def _action_indent(self):
        self.buffer.checkpoint()
        buf = self.buffer
        buf.lines[buf.cursor_row] = "    " + buf.current_line
        buf.cursor_col = min(buf.cursor_col + 4, len(buf.current_line))
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

    # placeholders, stuff i want to add but have no clue how so i will defo be watching some tutorials
    def _action_smart_tab(self) : pass
    def _action_clear_tab_stops(self): pass
    def _action_accept_autocomplete(self): pass
    def _action_execute_command(self): pass
    
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
            self._yank = list(buf.lines[r0 : r1 + 1])
        else:
            bounds = self._selection_bounds()
            if bounds is None:
                return
            r0, c0, r1, c1 = bounds
            if r0 == r1:
                self._yank = [buf.lines[r0][c0 : c1 + 1]]
            else:
                self._yank = (
                    [buf.lines[r0][c0:]]
                    + list(buf.lines[r0 + 1 : r1])
                    + [buf.lines[r1][: c1 + 1]]
                )
        self._action_enter_normal()
        # this looks very messy tbh, its not i promise

    def _action_delete_selection(self):
        buf = self.buffer
        buf.checkpoint()
        if self.msm.mode is Mode.VISUAL_LINE:
            if self.visual_anchor is None:
                return
            r0 = min(self.visual_anchor[0], buf.cursor_row)
            r1 = max(self.visual_anchor[0], buf.cursor_row)
            self._yank = list(buf.lines[r0 : r1 + 1])
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
            if r0 == r1:
                line = buf.lines[r0]
                self._yank = [line[c0 : c1 + 1]]
                buf.lines[r0] = line[:c0] + line[c1 + 1 :]
                buf.cursor_col = c0
            else:
                self._yank = (
                    [buf.lines[r0][c0:]]
                    + list(buf.lines[r0 + 1 : r1])
                    + [buf.lines[r1][: c1 + 1]]
                )
                buf.lines[r0] = buf.lines[r0][:c0] + buf.lines[r1][c1 + 1 :]
                del buf.lines[r0 + 1 : r1 + 1]
                buf.cursor_row = r0
                buf.cursor_col = c0
        buf.modified = True
        self._action_enter_normal()


