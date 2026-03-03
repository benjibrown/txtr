# core buffer management stuff, this is very much a wip still and doesnt do much without the frontend and parsing of cmds.

from __future__ import annotations

# buffer is clueless about the frontend btw
class Buffer:
    def __init__(self):
        self.lines = [""]
        self.cursor_row = 0
        self.cursor_col = 0
        self.modified = False
        self.path = None
        # will define later, this'll do for now...
        self._undo = []
        self._redo = []

    # undo/redo funcs, a very basic feature

    def checkpoint(self):
        # stack!!!!. i love fifo.
        self._undo.append((list(self.lines), self.cursor_row, self.cursor_col))
        self._redo.clear()

    def undo(self):
        if not self._undo:
            return False
        self._redo.append((list(self.lines), self.cursor_row, self.cursor_col))
        self.lines, self.cursor_row, self.cursor_col = self._undo.pop()
        self.modified = True
        return True

    def redo(self):
        if not self._redo:
            return False
        self._undo.append((list(self.lines), self.cursor_row, self.cursor_col))
        self.lines, self.cursor_row, self.cursor_col = self._redo.pop()
        self.modified = True
        return True


    # properties :)
    @property
    def current_line(self):
        return self.lines[self.cursor_row]

    @property
    def line_count(self):
        return len(self.lines)

    # manage cursor movement - clamping cursor to valid pos etc 
    def move(self, *, drow=0, dcol=0, clamp=True):
        self.cursor_row = max(0, min(self.cursor_row + drow, self.line_count - 1))
        max_col = len(self.lines[self.cursor_row])
        self.cursor_col = max(0, min(self.cursor_col + dcol, max_col))

    def move_to(self, row, col):
        row = max(0, min(row, self.line_count - 1))
        col = max(0, min(col, len(self.lines[row])))
        self.cursor_row, self.cursor_col = row, col

    def clamp_col(self):
        self.cursor_col = min(self.cursor_col, len(self.current_line))

    def first_nonblank(self):
        # hello whitespace 
        stripped = self.current_line.lstrip()
        return len(self.current_line) - len(stripped)

    
    # text insertion
    def insert(self, text):
        # inserts [text] at cursor pos.
        line = self.lines[self.cursor_row]
        before = line[: self.cursor_col]
        after = line[self.cursor_col :]
        full = before + text + after
        new = full.split("\n")
        self.lines[self.cursor_row : self.cursor_row + 1] = new
        self.cursor_row += len(new) - 1
        self.cursor_col = len(new[-1]) - len(after)
        self.modified = True

    def newline(self):
        line = self.current_line
        indent = self._leading_whitespace(line)
        rest = line[self.cursor_col :]
        self.lines[self.cursor_row] = line[: self.cursor_col]
        self.lines.insert(self.cursor_row + 1, indent + rest)
        self.cursor_row += 1
        self.cursor_col = len(indent)
        self.modified = True

    # all this is text deletion stuff
    def backspace(self):
        if self.cursor_col > 0:
            line = self.current_line
            self.lines[self.cursor_row] = line[: self.cursor_col - 1] + line[self.cursor_col :]
            self.cursor_col -= 1
        elif self.cursor_row > 0:
            prev = self.lines[self.cursor_row - 1]
            self.cursor_col = len(prev)
            self.lines[self.cursor_row - 1] = prev + self.current_line
            del self.lines[self.cursor_row]
            self.cursor_row -= 1
        self.modified = True

    def delete_char(self):
        line = self.current_line
        if self.cursor_col < len(line):
            self.lines[self.cursor_row] = line[: self.cursor_col] + line[self.cursor_col + 1 :]
            self.modified = True

    def delete_line(self):
        removed = [self.lines.pop(self.cursor_row)]
        if not self.lines:
            self.lines = [""]
        self.cursor_row = min(self.cursor_row, self.line_count - 1)
        self.cursor_col = min(self.cursor_col, len(self.current_line))
        self.modified = True
        return removed

    # opening and saving files, this is pretty straightforward. we read the whole file into memory, which is fine for small files but might be an issue for larger ones. can optimise later



    def load(self, path):
        try:
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            content = ""
        self.lines = content.splitlines() or [""]
        self.cursor_row = 0
        self.cursor_col = 0
        self.modified = False
        self.path = path
        self._undo.clear()
        self._redo.clear()

    def save(self, path=None): # if path is none then save to current path, if no current path then where tf are you? how are you actually running the editor lmao
        target = path or self.path
        if target is None:
            raise ValueError("No path given and buffer has no associated file.")
        with open(target, "w", encoding="utf-8") as fh:
            fh.write("\n".join(self.lines))
        self.path = target
        self.modified = False




    # helper funcs (only one rn so technically helper func)
    @staticmethod
    def _leading_whitespace(line):
        return line[: len(line) - len(line.lstrip())]



