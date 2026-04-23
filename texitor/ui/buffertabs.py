# this is very peak
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

    DEFAULT_CSS = """
    BufferTabs {
        height: 1;
        dock: top;
    }
    """

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._ranges = []
    # visible tabs :)
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

        return visible, labels
    # this code looks hard to read but its just building a text ojbect based on if the file is active or not
    def render_line(self, y):
        if y != 0:
            return Strip.blank(self.size.width)

        width = self.size.width
        visible, labels = self._visibleTabs(width)
        active = self._app.activeBufferIndex

        text = Text(no_wrap=True)
        self._ranges = []
        if visible and visible[0] > 0:
            text.append("< ", style=Style(color=_EDGE_FG, bgcolor=_BAR_BG, bold=True))

        for pos, idx in enumerate(visible):
            if text.cell_len and not text.plain.endswith(" "):
                text.append(" ", style=Style(bgcolor=_BAR_BG))
            label = labels[idx]
            start = text.cell_len
            if idx == active:
                text.append(f" {label} ", style=Style(color=_ACTIVE_FG, bgcolor=_ACTIVE_BG, bold=True))
            else:
                text.append(f" {label} ", style=Style(color=_BAR_FG, bgcolor=_INACTIVE_BG))
            self._ranges.append((start, text.cell_len, idx))

        if visible and visible[-1] < len(labels) - 1:
            if text.cell_len:
                text.append(" ", style=Style(bgcolor=_BAR_BG))
            text.append(" >", style=Style(color=_EDGE_FG, bgcolor=_BAR_BG, bold=True))

        text.append(" " * max(0, width - text.cell_len), style=Style(color=_BAR_FG, bgcolor=_BAR_BG))
        return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)

    def on_mouse_down(self, event):
        if event.button != 1:
            return
        for start, end, idx in self._ranges:
            if start <= event.x < end:
                self._app._activateBuffer(idx, notify=False)
                return
