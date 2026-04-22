from pathlib import Path
# rahhhh i love buffers
from texitor.core.buffer import Buffer
from texitor.ui.buffertabs import BufferTabs
from texitor.ui.editor import EditorWidget
from texitor.ui.statusbar import StatusBar


class BufferManagerMixin:

    def _canonicalPath(self, path):
        return str(Path(path).expanduser().resolve())
    # essentialy - is this a new, unsaved buffer with no content and no undo history ???/
    def _isPristineScratch(self, buf=None):
        buf = buf or self.buffer
        return ()
            buf.path is None
            and not buf.modified
            and buf.lines == [""]
            and not buf._undo
            and not buf._redo
        )

    def _unnamedBufferLabel(self, target_idx):
        unnamed = [idx for idx, buf in enumerate(self.buffers) if buf.path is None]
        if len(unnamed) <= 1:
            return "[No Name]"
        number = unnamed.index(target_idx) + 1
        return f"[No Name {number}]"

    def _bufferLabel(self, idx, max_len=None):
        buf = self.buffers[idx]
        name = Path(buf.path).name if buf.path else self._unnamedBufferLabel(idx)
        if max_len and len(name) > max_len:
            name = name[: max(1, max_len - 1)] + "…"
        if buf.modified:
            name += " ●" # if the buffer is modified, add a dot to the end of the name - just like neovim
        return name

    def _findBufferIndex(self, path, exclude_idx=None):
        canonical = self._canonicalPath(path)
        for idx, buf in enumerate(self.buffers):
            if idx == exclude_idx or not buf.path:
                continue
            if self._canonicalPath(buf.path) == canonical:
                return idx
        return None

    def _syncBufferWidgets(self):
        editor = self.query(EditorWidget).first(None)
        if editor:
            editor._buf = self.buffer
            editor._scroll_top = getattr(self.buffer, "view_scroll_top", 0)
        status = self.query(StatusBar).first(None)
        if status:
            status._buf = self.buffer
        tabs = self.query(BufferTabs).first(None)
        if tabs:
            tabs.refresh()

    def _clearBufferScopedUi(self):
        self.visual_anchor = None
        self._pending_key = ""
        self._commandSourceMode = None
        self._dismissAutocomplete()
    #
    # activate the buffer at a given index-  very nice
    def _activateBuffer(self, idx, notify=False):
        if idx < 0 or idx >= len(self.buffers):
            return False

        editor = self.query(EditorWidget).first(None)
        if editor:
            self.buffer.view_scroll_top = editor._scroll_top

        self.activeBufferIndex = idx
        self.buffer = self.buffers[idx]
        self._clearBufferScopedUi()
        self._syncBufferWidgets()


