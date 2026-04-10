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
    SEARCH = auto()


# Valid transitions: {from_mode: {to_mode, ...}}
_TRANSITIONS = {
    Mode.NORMAL: {Mode.INSERT, Mode.VISUAL, Mode.VISUAL_LINE, Mode.COMMAND, Mode.SEARCH},
    Mode.INSERT: {Mode.NORMAL},
    Mode.VISUAL: {Mode.NORMAL, Mode.COMMAND, Mode.SEARCH},
    Mode.VISUAL_LINE: {Mode.NORMAL, Mode.COMMAND, Mode.SEARCH},
    Mode.COMMAND: {Mode.NORMAL},
    Mode.SEARCH: {Mode.NORMAL},
}


class ModeStateMachine:
    def __init__(self):
        self._mode = Mode.NORMAL
        self.on_change = None  # optional callback(new_mode) set by app

    @property
    def mode(self):
        return self._mode

    def transition(self, target):
        allowed = _TRANSITIONS.get(self._mode, set())
        if target not in allowed:
            raise ValueError(f"Invalid transition: {self._mode} -> {target}")
        self._mode = target
        if self.on_change:
            try:
                self.on_change(target)
            except Exception:
                pass

    def is_normal(self): return self._mode is Mode.NORMAL
    def is_insert(self): return self._mode is Mode.INSERT
    def is_visual(self): return self._mode in (Mode.VISUAL, Mode.VISUAL_LINE)
    def is_command(self): return self._mode is Mode.COMMAND
    def is_search(self): return self._mode is Mode.SEARCH

    def __repr__(self):
        return f"ModeStateMachine({self._mode.name})"
