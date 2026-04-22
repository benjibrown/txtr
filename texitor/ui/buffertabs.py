from __future__ import annotations

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

from texitor.core.theme import theme as _theme

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)
_BAR_BG = _theme.bg_alt
_BAR_FG = _theme.fg_dim
_ACTIVE_FG = _theme.bg
_ACTIVE_BG = _theme.accent
_INACTIVE_BG = _theme.bg_popup
_EDGE_FG = _theme.fg_muted


class BufferTabs(Widget):

    DEFAULT_CSS = """"
    BufferTabs {}
        height: 1;
        dock: top;
    }
    """

    def __init__(self, app):
        super().__init__()
        self._app = app

    def _visibleTabs(self, width):
        count = len(self._app.buffers)
        active = self._app.activeBufferIndex
        labels = [self._app._bufferLabel(idx, max_len=24) for idx in range(count)]
        sizes = [len(label) + 2 for label in labels]
        total = sum(sizes) + max(0, count - 1)
        if total <= width:
            return list(range(count)), labels

        visible = [active]
        used = sizes[active]
        left = active - 1
        right = active + 1

        while True:
            added = False
            if right < count:
                markers = 2 if left >= 0 else 0
                markers += 2 if right + 1 < count else 0
                need = sizes[right] + 1
                if used + need + markers <= width:
                    visible.append(right)
                    used += need
                    right += 1
                    added = True
            if left >= 0:
                markers = 2 if left - 1 >= 0 else 0
                markers += 2 if right < count else 0
                need = sizes[left] + 1
                if used + need + markers <= width:
                    visible.insert(0, left)
                    used += need
                    left -= 1
                    added = True
            if not added:
                break

