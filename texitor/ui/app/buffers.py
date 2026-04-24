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
        return (
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
            tabs.display = len(self.buffers) > 1
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
        if idx == self.activeBufferIndex:
            if notify:
                self.notify(f"already on {self._bufferLabel(idx)}", timeout=2)
            return True

        editor = self.query(EditorWidget).first(None)
        if editor:
            self.buffer.view_scroll_top = editor._scroll_top

        self.activeBufferIndex = idx
        self.buffer = self.buffers[idx]
        self._clearBufferScopedUi()
        self._syncBufferWidgets()

        # praying this actually works lol 
        if self.buffer.path:
            self._loadBibsForFile(self.buffer.path, quiet=True)
        else:
            self.citeCompleter.clear()
            self._bibSignature = ()
            self._stopBibAutoscan()
        self._refresh_all()
        if notify:
            self.notify(f"switched to {self._bufferLabel(idx)}", timeout=2)
        return True

    def _openBufferPath(self, path, notify=False):
        canonical = self._canonicalPath(path)
        existing = self._findBufferIndex(canonical)
        if existing is not None:
            if existing == self.activeBufferIndex:
                if notify:
                    self.notify(f"{Path(canonical).name} is already open", timeout=2)
                return "already-open"
            self._activateBuffer(existing, notify=False)
            if notify:
                self.notify(f"{Path(canonical).name} is already open - switched to it", timeout=2)
            return "switched"

        if len(self.buffers) == 1 and self.activeBufferIndex == 0 and self._isPristineScratch():
            self.buffer.load(canonical)
            self._syncBufferWidgets()
            self._loadBibsForFile(canonical)
            self._refresh_all()
            if notify:
                self.notify(f"opened {Path(canonical).name}", timeout=2)
            return "opened"

        buf = Buffer() # instanitate !!
        buf.load(canonical)
        self.buffers.append(buf)
        self._activateBuffer(len(self.buffers) - 1, notify=False)
        if notify:
            self.notify(f"opened {Path(canonical).name}", timeout=2)
        return "opened"

    def _newScratchBuffer(self):
        buf = Buffer()
        self.buffers.append(buf)
        return self._activateBuffer(len(self.buffers) - 1, notify=True)

    def _nextBuffer(self):
        if len(self.buffers) <= 1:
            self.notify("no buffers to switch to or open", severity="warning")
            return False
        self._activateBuffer((self.activeBufferIndex + 1) % len(self.buffers))
        return True

    def _prevBuffer(self):
        if len(self.buffers) <= 1:
            self.notify("no buffers to switch to or open", severity="warning")
            return False
        self._activateBuffer((self.activeBufferIndex - 1) % len(self.buffers))
        return True

    def _hasModifiedBuffers(self):
        return any(buf.modified for buf in self.buffers) # i hope u actually did some editing if u see this message

    def _bufferRows(self):
        rows = [("header", "Open buffers")]
        for idx, buf in enumerate(self.buffers):
            path = buf.path or self._unnamedBufferLabel(idx)
            right = "active" if idx == self.activeBufferIndex else "hidden"
            rows.append(("row", self._bufferLabel(idx), right, ("buffer-switch", idx)))
            rows.append(("text", path))
        return rows

    def _closeBuffer(self, idx=None, force=False):
        idx = self.activeBufferIndex if idx is None else idx
        if idx < 0 or idx >= len(self.buffers):
            return False

        buf = self.buffers[idx]
        watched = buf.path and buf.path == self._watchBufferPath
        if buf.modified and not force:
            self.notify(f"{self._bufferLabel(idx)} has unsaved changes - use :q! to force close", severity="warning")
            return False

        if len(self.buffers) == 1:
            if self._isPristineScratch(buf):
                self.notify("last buffer is already empty", severity="warning")
                return False
            self.buffers[0] = Buffer()
            self.activeBufferIndex = 0
            self.buffer = self.buffers[0]
            self._clearBufferScopedUi()
            if watched:
                self._watchActive = False
                self._watchBufferPath = None
                self._buildStatus = ""
            self._syncBufferWidgets()
            self.citeCompleter.clear()
            self._bibSignature = ()
            self._stopBibAutoscan()
            self._refresh_all()
            return True

        closing_active = idx == self.activeBufferIndex
        del self.buffers[idx]
        if watched:
            self._watchActive = False
            self._watchBufferPath = None
            self._buildStatus = ""
        if idx < self.activeBufferIndex:
            self.activeBufferIndex -= 1
        elif idx >= len(self.buffers):
            self.activeBufferIndex = len(self.buffers) - 1

        if closing_active:
            return self._activateBuffer(self.activeBufferIndex, notify=True)

        self.buffer = self.buffers[self.activeBufferIndex]
        self._syncBufferWidgets()
        self._refresh_all()
        return True
