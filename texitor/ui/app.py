
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

