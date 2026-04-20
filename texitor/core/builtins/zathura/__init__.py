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

