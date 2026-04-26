from __future__ import annotations

from texitor.core.cmdregistry import command
from texitor.core.config import config as cfg


class FileCommandsMixin:

    def _saveBuffer(self, buf, target=None, notify=True, autocompile=False):
        import texitor.core.recents as _recents
        from texitor.core.plugins import pluginLoader

        old_path = buf.path
        path = target or buf.path
        if not path:
            return False

        if target:
            buf.save(target)
            path = target
        else:
            buf.save()
            path = buf.path

        if notify:
            self.notify(f"saved {path}")
        _recents.push(path)
        self._saveCursorState(buf)
        if buf is self.buffer:
            self._loadBibsForFile(path, quiet=True)
        pluginLoader.fireSave(self, path)

        watched_old = self._watchActive and old_path and self._watchBufferPath == old_path
        watched_new = self._watchActive and self._watchBufferPath == path
        if watched_old:
            self._watchBufferPath = path
        if watched_old or watched_new:
            self._watchLastRevision[path] = buf.revision

        mode = cfg.get("compiler", "autocompile", "save")
        if mode is True:
            mode = "save"
        elif mode is False:
            mode = "off"

        if autocompile and (mode == "always" or (mode == "save" and buf.build_primed)):
            self._cmd_build("")
        return True

    def _saveAllBuffers(self, force=False):
        # this just saves the whole little pile of buffers if they actually have names
        modified = [(idx, buf) for idx, buf in enumerate(self.buffers) if buf.modified]
        unnamed = [(idx, buf) for idx, buf in modified if not buf.path]
        if unnamed and not force:
            self.notify(
                f"{self._bufferLabel(unnamed[0][0])} has no file name - save it first or use :wqa! to force quit all",
                severity="warning",
            )
            return False

        saved = 0
        for _, buf in modified:
            if not buf.path:
                continue
            self._saveBuffer(buf, notify=False, autocompile=(buf is self.buffer))
            saved += 1

        if saved:
            self.notify(f"saved {saved} buffer{'s' if saved != 1 else ''}")
        elif not force:
            self.notify("nothing to save")
        return True

    def _quitCurrent(self, force=False):
        if len(self.buffers) > 1:
            return self._closeBuffer(force=force)
        if self.buffer.modified and not force:
            self.notify("unsaved changes - use :q! to force quit", severity="warning")
            return False
        self.exit()
        return True

    # file commands - the nice stuff fr 
    @command(":w", "save current buffer", section="File")
    def _cmd_write(self, args):
        from pathlib import Path

        if args:
            target = self._canonicalPath(Path(args).expanduser())
            existing = self._findBufferIndex(target, exclude_idx=self.activeBufferIndex)
            if existing is not None:
                self.notify(f"'{Path(target).name}' is already open in another buffer", severity="warning")
                return False
            return self._saveBuffer(self.buffer, target=target, autocompile=True)
        if not self.buffer.path:
            self.notify("no file name - use :w <filename>", severity="warning")
            return False
        return self._saveBuffer(self.buffer, autocompile=True)

    @command(":wq", "save current buffer, then close it or quit if it is the last one", section="File", aliases=[":x", "imstuckintxtrpleasehelpme"], hidden=True)
    def _cmd_wq(self, args):
        if not self._cmd_write(""):
            return
        self._quitCurrent(force=False)

    @command(":wa", "save all modified named buffers", section="File", hidden=True)
    def _cmd_writeAll(self, args):
        self._saveAllBuffers(force=False)

    @command(":wqa", "save all modified named buffers, then quit all", section="File", hidden=True)
    def _cmd_writeQuitAll(self, args):
        if not self._saveAllBuffers(force=False):
            return
        self.exit()

    @command(":wqa!", "save all named buffers you can, then force quit all", section="File", hidden=True)
    def _cmd_writeQuitAllForce(self, args):
        self._saveAllBuffers(force=True)
        self.exit()

    @command(":a", "modifier  •  can be stacked with other commands to apply them to all buffers", section="File")
    def _cmd_allModifier(self, args):
        self.notify(":a needs to be stacked with another command, like :wa or :qa", severity="warning")

    @command(":q", "close current buffer, or quit txtr if it is the last one", section="File")
    def _cmd_quit(self, args):
        self._quitCurrent(force=False)

    @command(":q!", "force close current buffer, or force quit txtr if it is the last one", section="File")
    def _cmd_forceQuit(self, args):
        self._quitCurrent(force=True)

    @command(":qa", "quit all open buffers and exit txtr", section="File", hidden=True)
    def _cmd_quitAll(self, args):
        if self._hasModifiedBuffers():
            self.notify("unsaved changes - use :qa! to force quit all", severity="warning")
            return
        self.exit()

    @command(":qa!", "force quit all open buffers without saving", section="File", hidden=True)
    def _cmd_forceQuitAll(self, args):
        self.exit()

    @command(":e <file>", "open file", section="File")
    def _cmd_edit(self, args):
        from pathlib import Path

        if args:
            target = Path(args).expanduser()
            if target.exists() and target.is_dir():
                self.notify(f"cannot open directory: {target}", severity="warning")
                return
            path = self._canonicalPath(target)
            self._openBufferPath(path, notify=True)
            import texitor.core.recents as _recents
            _recents.push(path)
        else:
            self.notify(":e <filename>", severity="warning")

    @command(":bn", "switch to next open buffer", section="File")
    def _cmd_bufferNext(self, args):
        self._nextBuffer()

    @command(":bp", "switch to previous open buffer", section="File")
    def _cmd_bufferPrev(self, args):
        self._prevBuffer()

    @command(":buffers", "show the open buffer list", section="File", aliases=[":ls"])
    def _cmd_buffers(self, args):
        self._openInfoPanel("buffers", self._bufferRows(), footer="  enter open   q close")

    @command(":explore", "open the file explorer in the current file directory", section="File", aliases=[":ex"])
    def _cmd_explore(self, args):
        from pathlib import Path
        from texitor.ui.fileexplorer import FileExplorer

        base = None
        if args:
            base = Path(args).expanduser()
        elif self.buffer.path:
            base = Path(self.buffer.path).expanduser().parent
        else:
            base = Path.cwd()

        self._closeOverlayPanels(except_name="explorer")
        self.explorerOpen = True
        self.query_one(FileExplorer).open(base)

    @command(":bib", "reload .bib files from current file's directory", section="File")
    def _cmd_bib(self, args):
        path = self.buffer.path
        if not path:
            self.notify("no file open", severity="warning")
            return
        self._loadBibsForFile(path, fromcmd=True)
