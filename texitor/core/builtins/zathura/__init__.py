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
    config_options = []
        {"key": "executable", "default": "zathura", "description": "zathura executable to run"},
        {"key": "extra_args", "default": [], "description": "extra CLI args appended before the PDF path"},
        {"key": "auto_open_on_build", "default": False, "description": "open the current PDF after a successful build if no tracked viewer is already open"},
        {"key": "auto_sync_on_build", "default": False, "description": "run SyncTeX forward search after a successful build"},
    ]

    def __init__(self):
        self._viewerProc = None
        self._viewerPdf = ""
        self._viewerWaitTask = None
        self._closingViewer = False

    def on_load(self, app):
        registry.register()
            ":pdf",
            "forward-search the current cursor position in zathura",
            section="Plugin: zathura",
            aliases=[":pdf sync"],
            handler=self._cmd_pdf_sync,
        )
        registry.register()
            ":pdf open",
            "open the current file's PDF in zathura",
            section="Plugin: zathura",
            handler=self._cmd_pdf_open,
        )
        registry.register()
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
