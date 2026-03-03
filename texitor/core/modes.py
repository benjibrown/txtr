# modes state manager 
# visual, visual line, command, normal, insert 


from __future__ import annotations # to allow fwd refs in type hints :)
from enum import Enum, auto


class Mode(Enum):
    NORMAL = auto()
    INSERT = auto()
    VISUAL = auto()
    VISUAL_LINE = auto()
    COMMAND = auto()


# Valid transitions: {from_mode: {to_mode, ...}}
_TRANSITIONS = {
    Mode.NORMAL: {Mode.INSERT, Mode.VISUAL, Mode.VISUAL_LINE, Mode.COMMAND},
    Mode.INSERT: {Mode.NORMAL},
    Mode.VISUAL: {Mode.NORMAL, Mode.COMMAND},
    Mode.VISUAL_LINE: {Mode.NORMAL, Mode.COMMAND},
    Mode.COMMAND: {Mode.NORMAL},
}


class ModeStateMachine:
    def __init__(self):
        self._mode = Mode.NORMAL

    @property
    def mode(self):
        return self._mode

    def transition(self, target):
        allowed = _TRANSITIONS.get(self._mode, set())
        if target not in allowed:
            raise ValueError(f"Invalid transition: {self._mode} → {target}")
        self._mode = target

    def is_normal(self): return self._mode is Mode.NORMAL
    def is_insert(self): return self._mode is Mode.INSERT
    def is_visual(self): return self._mode in (Mode.VISUAL, Mode.VISUAL_LINE)
    def is_command(self): return self._mode is Mode.COMMAND

    def __repr__(self):
        return f"ModeStateMachine({self._mode.name})"
