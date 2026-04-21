from __future__ import annotations

import asyncio
import shutil

from texitor.core.cmdregistry import registry
from texitor.core.config import config as cfg
from texitor.core.plugins import PluginBase

from .helpers import (
    buildOpenCommand,
    buildSyncCommand,
    normalizeExtraArgs,
    pdfPath,
    sourcePath,
    synctexPath,
)
#TODO - support more viewers 

# W plugin???
class ZathuraPlugin(PluginBase):
    name = "zathura"
    description = "open PDFs in zathura and jump to the current source location with SyncTeX"
    version = "0.1.0"
    author = "benjibrown"
    config_section = "zathura"
    commands = [
        (":pdf", "forward-search the current cursor position in zathura"),
        (":pdf open", "open the current file's PDF in zathura"),
        (":pdf sync", "forward-search the current cursor position in zathura"),
        (":pdf close", "close the zathura window launched by txtr"),
    ]
    config_options = [
        {"key": "executable", "default": "zathura", "description": "zathura executable to run"},
        {"key": "extra_args", "default": [], "description": "extra CLI args appended before the PDF path"},
        {"key": "auto_open_on_build", "default": False, "description": "open the current PDF after a successful build if no tracked viewer is already open"},
        {"key": "auto_sync_on_build", "default": False, "description": "run SyncTeX forward search after a successful build"},
    ]

    def __init__(self):
        # viewer states and allat
        self._viewerProc = None
        self._viewerPdf = ""
        self._viewerWaitTask = None
        self._closingViewer = False

    def on_load(self, app):
        registry.register(
            ":pdf",
            "forward-search the current cursor position in zathura",
            section="Plugin: zathura",
            aliases=[":pdf sync"],
            handler=self._cmd_pdf_sync,
        )
        registry.register(
            ":pdf open",
            "open the current file's PDF in zathura",
            section="Plugin: zathura",
            handler=self._cmd_pdf_open,
        )


        registry.register(
            ":pdf close",
            "close the zathura window launched by txtr",
            section="Plugin: zathura",
            handler=self._cmd_pdf_close,
        )

    def on_unload(self, app):
        registry.unregisterSection("Plugin: zathura")
        if self._viewerRunning():
            self._closingViewer = True
            self._viewerProc.terminate()
        self._clearViewerState()

    def on_build_done(self, app, rc):

        if rc != 0:
            return
        settings = self._settings()
        if settings["auto_sync_on_build"]:
            asyncio.create_task(self._runSync(app, notify=False))
        elif settings["auto_open_on_build"]:
            asyncio.create_task(self._runOpen(app, notify=False))

    def _cmd_pdf_open(self, app, args):

        asyncio.create_task(self._runOpen(app))

    def _cmd_pdf_sync(self, app, args):
        asyncio.create_task(self._runSync(app))


    def _cmd_pdf_close(self, app, args):

        asyncio.create_task(self._runClose(app))
    


    def _settings(self):
        settings = self.config()
        settings.setdefault("executable", "zathura")
        settings["extra_args"] = normalizeExtraArgs(settings.get("extra_args", []))
        settings.setdefault("auto_open_on_build", False)
        settings.setdefault("auto_sync_on_build", False)
        return settings

    def _clearViewerState(self):
        current = asyncio.current_task()
        self._viewerProc = None
        self._viewerPdf = ""
        if self._viewerWaitTask and self._viewerWaitTask is not current and not self._viewerWaitTask.done():
            self._viewerWaitTask.cancel()
        self._viewerWaitTask = None
        self._closingViewer = False

    def _viewerRunning(self):
        if self._viewerProc is None:
            return False
        if self._viewerProc.returncode is not None:

            self._clearViewerState()
            return False
        return True


    # insane levels of validation fr 

    def _currentPaths(self, app):
        ctx = self.context(app)
        file_path = ctx.file_path
        if not file_path:
            self.notify(app, "save and build the file first before using :pdf", severity="warning")
            return None, None, None
        tex_path = sourcePath(file_path)
        return ctx, tex_path, pdfPath(file_path)

    def _missingExecutable(self, app, settings):
        if shutil.which(settings["executable"]) is None:

            self.notify(app, f"zathura executable not found: {settings['executable']}", severity="error")
            return True

        return False


    def _missingPdf(self, app, pdf_path):
        if not pdf_path.exists():
            self.notify(app, f"pdf not found: {pdf_path.name} - run :build first", severity="warning")
            return True
        return False

    def _missingSynctex(self, app, tex_path):
        engine = cfg.get("compiler", "engine", "latexmk")
        aux_dir = cfg.get("compiler", "aux_dir", ".aux")
        sync_path = synctexPath(tex_path, engine, aux_dir)
        if sync_path.exists():
            return False
        self.notify(app, "SyncTeX data not found - rebuild with a txtr compiler preset or a custom command that enables synctex", severity="warning", timeout=5)
        return True

    def _warnModified(self, app, ctx):
        if ctx.modified:
            self.notify(app, "unsaved changes - PDF sync uses the last built version", severity="warning")

    async def _spawnTracked(self, app, cmd, pdf_path):
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self.notify(app, f"zathura executable not found: {cmd[0]}", severity="error")
            return False
        self._viewerProc = proc
        self._viewerPdf = str(pdf_path)
        self._viewerWaitTask = asyncio.create_task(self._watchViewer(app, proc))
        return True

    async def _spawnOneShot(self, app, cmd): # one shot???? future cat reference 
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
        except FileNotFoundError:
            self.notify(app, f"zathura executable not found: {cmd[0]}", severity="error")
            return False
        asyncio.create_task(self._waitOneShot(app, proc))
        return True

    async def _watchViewer(self, app, proc):
        rc = await proc.wait()
        closing = self._closingViewer
        if self._viewerProc is proc:
            self._clearViewerState()
        if rc not in (0, None) and not closing:
            self.notify(app, f"zathura exited with code {rc}", severity="warning")

    async def _waitOneShot(self, app, proc):
        rc = await proc.wait()
        if rc not in (0, None):
            self.notify(app, f"zathura sync failed (exit {rc})", severity="warning")

    async def _runOpen(self, app, notify=True):
        ctx, tex_path, pdf_path = self._currentPaths(app)
        if not tex_path:
            return False
        settings = self._settings()
        if self._missingExecutable(app, settings) or self._missingPdf(app, pdf_path):
            return False
        self._warnModified(app, ctx)

        if self._viewerRunning() and self._viewerPdf == str(pdf_path):
            if notify:
                self.notify(app, f"zathura already open for {pdf_path.name}")
            return True

        if self._viewerRunning():
            await self._runClose(app, notify=False)

        opened = await self._spawnTracked(app, buildOpenCommand(settings, pdf_path), pdf_path)
        if opened and notify:
            self.notify(app, f"opened {pdf_path.name} in zathura", timeout=4)
        return opened
    # im hungry 
    async def _runSync(self, app, notify=True):
        ctx, tex_path, pdf_path = self._currentPaths(app)
        if not tex_path:
            return False
        settings = self._settings()
        if self._missingExecutable(app, settings) or self._missingPdf(app, pdf_path):
            return False
        if self._missingSynctex(app, tex_path):
            return False
        self._warnModified(app, ctx)

        cmd = buildSyncCommand(settings, tex_path, pdf_path, ctx.cursor_row, ctx.cursor_col)

        if not self._viewerRunning():
            synced = await self._spawnTracked(app, cmd, pdf_path)
        elif self._viewerPdf != str(pdf_path):
            await self._runClose(app, notify=False)
            synced = await self._spawnTracked(app, cmd, pdf_path)
        else:
            synced = await self._spawnOneShot(app, cmd)

        if synced and notify:
            self.notify(app, f"synced {pdf_path.name} in zathura", timeout=4)
        return synced

    async def _runClose(self, app, notify=True):
        if not self._viewerRunning():
            self._clearViewerState()
            if notify:
                self.notify(app, "no txtr-launched zathura window is open", severity="warning") # why would u even close it bruh
            return False

        self._closingViewer = True
        self._viewerProc.terminate()
        try:
            await asyncio.wait_for(self._viewerProc.wait(), timeout=2)
        except asyncio.TimeoutError:
            self._viewerProc.kill()
            await self._viewerProc.wait()
        self._clearViewerState()
        if notify:
            self.notify(app, "closed zathura", timeout=3)
        return True


plugin = ZathuraPlugin
