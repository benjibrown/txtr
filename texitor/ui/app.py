
# main app.
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.events import Key

from texitor.core.buffer import Buffer
from texitor.core.keybinds import KeybindRegistry
from texitor.core.modes import Mode, ModeStateMachine
from texitor.ui.editor import EditorWidget
from texitor.ui.statusbar import StatusBar


class TxtrApp(App):
    # main app class - the big boy class that holds all of my janky code together...

    TITLE = "txtr" # aka texitor but who wants to type allat
    ENABLE_COMMAND_PALETTE = False
    CSS = "Screen { }"

    def __init__(self, filename: str | None = None):
        super().__init__()
        self.buffer = Buffer()
        self.msm = ModeStateMachine()
        self.keybinds = KeybindRegistry()
        self._yank = []
        self.visual_anchor = None 
        self._pending_key = ""   # accumulates multi-key sequences e.g. "g", "d"
        self._awaiting_replace: bool = False  # True after `r` — next key replaces char

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


