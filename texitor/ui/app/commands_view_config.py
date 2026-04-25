from __future__ import annotations

from texitor.core.cmdregistry import command
from texitor.core.config import config as cfg


class ViewConfigCommandsMixin:

    # this file is just all the calmer commands so commands.py stops screaming at me
    @command(":help", "open help menu", section="View", aliases=[":h"])
    def _cmd_help(self, args):
        self._action_open_help()

    @command(":snippets", "open snippets tab", section="View", aliases=[":snips"])
    def _cmd_snippets(self, args):
        from texitor.ui.helpmenu import HelpMenu

        self._closeOverlayPanels(except_name="help")
        self.helpOpen = True
        menu = self.query_one(HelpMenu)
        menu.open()
        menu.nextTab()

    @command(":config", "open config panel", section="View", aliases=[":config show"])
    def _cmd_configShow(self, args):
        from texitor.ui.configpanel import ConfigPanel

        self._closeOverlayPanels(except_name="config")
        self.configOpen = True
        self.query_one(ConfigPanel).open()

    @command(":set wrap", "enable soft line wrapping", section="View")
    def _cmd_setWrap(self, args):
        from texitor.ui.editor import EditorWidget

        cfg.set("editor", "wrap", True)
        self.query_one(EditorWidget).rebuildVisualLines()
        self._refresh_all()
        self.notify("wrap on")

    @command(":set nowrap", "disable soft line wrapping", section="View")
    def _cmd_setNowrap(self, args):
        from texitor.ui.editor import EditorWidget

        cfg.set("editor", "wrap", False)
        self.query_one(EditorWidget).rebuildVisualLines()
        self._refresh_all()
        self.notify("wrap off")

    # config commands - small but very useful fr
    @command(":config set <section.key> <value>", "set a config value", section="Config")
    def _cmd_configSet(self, args):
        from texitor.ui.app import _coerceValue, _resolveConfigKey

        parts = args.split(None, 1)
        if len(parts) != 2:
            self.notify(":config set <section.key> <value>", severity="warning")
            return
        dotKey, rawVal = parts
        section, key = _resolveConfigKey(dotKey)
        if section is None:
            self.notify(f"config: unknown key '{dotKey}'", severity="warning")
            return
        value = _coerceValue(rawVal)
        cfg.set(section, key, value)
        self.notify(f"config: {section}.{key} = {value}")
        if section == "citations" and self.buffer.path:
            self._loadBibsForFile(self.buffer.path, quiet=True)

    @command(":config append <section.key> <value>", "append a value to a list config entry", section="Config")
    def _cmd_configAppend(self, args):
        from texitor.ui.app import _coerceValue, _resolveConfigKey

        parts = args.split(None, 1)
        if len(parts) != 2:
            self.notify(":config append <section.key> <value>", severity="warning")
            return
        dotKey, rawVal = parts
        section, key = _resolveConfigKey(dotKey)
        if section is None:
            self.notify(f"config: unknown key '{dotKey}'", severity="warning")
            return
        value = _coerceValue(rawVal)
        cfg.append(section, key, value)
        current = cfg.get(section, key)
        self.notify(f"config: {section}.{key} = {current}")
        if section == "citations" and self.buffer.path:
            self._loadBibsForFile(self.buffer.path, quiet=True)

    @command(":config get <section.key>", "get a config value", section="Config")
    def _cmd_configGet(self, args):
        from texitor.ui.app import _resolveConfigKey

        if not args:
            self.notify(":config get <section.key>", severity="warning")
            return
        section, key = _resolveConfigKey(args)
        if section is None:
            self.notify(f"config: unknown key '{args}'", severity="warning")
            return
        val = cfg.get(section, key)
        if val is None:
            self.notify(f"config: {section}.{key} not set", severity="warning")
        else:
            self.notify(f"{section}.{key} = {val}")
