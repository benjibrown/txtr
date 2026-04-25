from __future__ import annotations

from texitor.core.cmdregistry import registry

from texitor.ui.app.commands_compiler import CompilerCommandsMixin
from texitor.ui.app.commands_file import FileCommandsMixin
from texitor.ui.app.commands_plugins import PluginCommandsMixin
from texitor.ui.app.commands_view_config import ViewConfigCommandsMixin


class CommandsMixin(
    FileCommandsMixin,
    ViewConfigCommandsMixin,
    CompilerCommandsMixin,
    PluginCommandsMixin,
):
    # thank god this file is not a novel anymore

    _SECTION_ORDER = ["File", "View", "Config", "Compiler", "Plugins"]

    def _action_execute_command(self):
        from texitor.core.plugins import pluginContext

        cmd = self.cmd_input.strip()
        source_mode = getattr(self, "_commandSourceMode", None) or self.msm.mode
        self._commandContext = pluginContext(self, mode_override=source_mode)
        try:
            if not registry.dispatch(self, cmd):
                self.notify(f"unknown command: {cmd}", severity="warning")
        finally:
            self._commandContext = None
            if self.msm.is_command():
                self._action_enter_normal()

    def _registerCommands(self):
        # this just scoops up every decorated command method from the mixins
        methods = [
            (name, getattr(self.__class__, name))
            for name in dir(self.__class__)
            if hasattr(getattr(self.__class__, name, None), "_cmd_meta")
        ]

        def _key(item):
            meta = item[1]._cmd_meta
            idx = self._SECTION_ORDER.index(meta["section"]) if meta["section"] in self._SECTION_ORDER else 99
            return (idx, meta.get("order", 0))

        methods.sort(key=_key)
        for name, method in methods:
            meta = method._cmd_meta
            bound = lambda app, args, m=method: m(app, args)
            registry.register(
                meta["syntax"],
                meta["description"],
                section=meta["section"],
                aliases=meta["aliases"] or None,
                hidden=meta.get("hidden", False),
                handler=bound,
            )

    # panel helpers live here because everyone and their dog calls them
    def _openInfoPanel(self, title, rows, footer=None):
        from texitor.ui.infopanel import InfoPanel

        self._closeOverlayPanels(except_name="info")
        self.infoOpen = True
        self.query_one(InfoPanel).open(title, rows, footer=footer)

    def _setInfoPanelRows(self, rows, footer=None):
        from texitor.ui.infopanel import InfoPanel

        self._closeOverlayPanels(except_name="info")
        self.infoOpen = True
        self.query_one(InfoPanel).setRows(rows, footer=footer)

    def _appendInfoPanelText(self, text, autoScroll=True):
        from texitor.ui.infopanel import InfoPanel

        self._closeOverlayPanels(except_name="info")
        self.infoOpen = True
        self.query_one(InfoPanel).appendText(text, autoScroll=autoScroll)

    def _appendInfoPanelStatus(self, text, level="info", autoScroll=True):
        from texitor.ui.infopanel import InfoPanel

        self._closeOverlayPanels(except_name="info")
        self.infoOpen = True
        self.query_one(InfoPanel).appendRow(("status", text, level), autoScroll=autoScroll)
