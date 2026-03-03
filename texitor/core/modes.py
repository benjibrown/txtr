"""Modal editing state machine.

Five modes, matching Vim/Neovim conventions:
  NORMAL       — default, navigation and commands
  INSERT       — text input
  VISUAL       — character-wise selection
  VISUAL_LINE  — line-wise selection
  COMMAND      — : command line
"""

from __future__ import annotations
from enum import Enum, auto


class Mode(Enum):
    NORMAL      = auto()
    INSERT      = auto()
    VISUAL      = auto()
    VISUAL_LINE = auto()
    COMMAND     = auto()


# Valid transitions: {from_mode: {to_mode, ...}}
_TRANSITIONS: dict[Mode, set[Mode]] = {
    Mode.NORMAL:      {Mode.INSERT, Mode.VISUAL, Mode.VISUAL_LINE, Mode.COMMAND},
    Mode.INSERT:      {Mode.NORMAL},
    Mode.VISUAL:      {Mode.NORMAL, Mode.COMMAND},
    Mode.VISUAL_LINE: {Mode.NORMAL, Mode.COMMAND},
    Mode.COMMAND:     {Mode.NORMAL},
}


