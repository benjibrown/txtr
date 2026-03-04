# statusbar - mode pill, filename, position

from __future__ import annotations

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.buffer import Buffer
from texitor.core.modes import Mode, ModeStateMachine

_CONSOLE = Console(
    width=500, no_color=False, highlight=False, markup=False, emoji=False
)

# (label, fg, bg) per mode — catppuccin mocha, i will not apologize for this choice, catppuccin is love, catppuccin is life 
# TODO - configurable themes :)
_MODE_STYLE = {
    Mode.NORMAL:      ("NORMAL",      "#1e1e2e", "#89b4fa"),   # blue
    Mode.INSERT:      ("INSERT",      "#1e1e2e", "#a6e3a1"),   # green
    Mode.VISUAL:      ("VISUAL",      "#1e1e2e", "#cba6f7"),   # mauve
    Mode.VISUAL_LINE: ("VISUAL LINE", "#1e1e2e", "#cba6f7"),
    Mode.COMMAND:     ("COMMAND",     "#1e1e2e", "#f38ba8"),   # red
}

_BAR_BG  = "#181825"
_BAR_FG  = "#cdd6f4"
_POS_BG  = "#313244"


