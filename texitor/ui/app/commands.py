# commands mixin - all : command handlers for TxtrApp
# each handler is decorated with @command so the registry can wire it up at mount
# _action_execute_command is a pure registry dispatch - no if/elif chains
# plugins follow the same pattern: decorate a function and call registry.register()

from __future__ import annotations
import asyncio

import texitor.core.compiler as _compiler
from texitor.core.config import config as cfg
from texitor.core.cmdregistry import registry, command


class CommandsMixin:

    def _action_execute_command(self):
        cmd = self.cmd_input.strip()
        self._action_enter_normal()
        if not registry.dispatch(self, cmd):
            self.notify(f"unknown command: {cmd}", severity="warning")

    # wires all @command-decorated methods into the registry at app mount.
    # methods are sorted by section order then definition order so the help menu is consistent.
    _SECTION_ORDER = ["File", "View", "Config", "Compiler"]

    def _registerCommands(self):
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
            # method is unbound - pass self (the app) as first arg
            bound = lambda app, args, m=method: m(app, args)
            registry.register(
                meta["syntax"],
                meta["description"],
                section=meta["section"],
                aliases=meta["aliases"] or None,
                handler=bound,
            )

        
    # file commands

    @command(":w", "save file", section="File")
    def _cmd_write(self, args):
        if args:
            self.buffer.save(args)
            self.notify(f"saved {args}")
            return
        if not self.buffer.path:
            self.notify("no file name - use :w <filename>", severity="warning")
            return
        self.buffer.save()
        self.notify(f"saved {self.buffer.path}")
        mode = cfg.get("compiler", "autocompile", "save")
        if mode is True:
            mode = "save"
        elif mode is False:
            mode = "off"
        if mode == "always" or (mode == "save" and self._buildPrimed):
            self._cmd_build("")

    @command(":wq", "save and quit", section="File", aliases=[":x", "imstuckintxtrpleasehelpme"])
    def _cmd_wq(self, args):
        self._cmd_write("")
        self.exit()

    @command(":q", "quit (warns if unsaved)", section="File")
    def _cmd_quit(self, args):
        if self.buffer.modified:
            self.notify("unsaved changes - use :q! to force quit", severity="warning")
            return
        self.exit()

    @command(":q!", "force quit without saving", section="File")
    def _cmd_forceQuit(self, args):
        self.exit()

    @command(":e <file>", "open file", section="File")
    def _cmd_edit(self, args):
        if args:
            self.buffer.load(args)
            import texitor.core.recents as _recents
            _recents.push(args)
            self._refresh_all()
        else:
            self.notify(":e <filename>", severity="warning")

    # view commands

    @command(":help", "open help menu", section="View", aliases=[":h"])
    def _cmd_help(self, args):
        self._action_open_help()

    @command(":snippets", "open snippets tab", section="View", aliases=[":snips"])
    def _cmd_snippets(self, args):
        from texitor.ui.helpmenu import HelpMenu
        self.helpOpen = True
        menu = self.query_one(HelpMenu)
        menu.open()
        menu.nextTab()

    @command(":config", "open config panel", section="View", aliases=[":config show"])
    def _cmd_configShow(self, args):
        from texitor.ui.configpanel import ConfigPanel
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

    # config commands

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

    # build commands

    @command(":build", "build with configured engine", section="Compiler", aliases=[":compile", ":b"])
    def _cmd_build(self, args):
        from texitor.ui.buildpanel import BuildPanel
        from texitor.ui.statusbar import StatusBar

        engine = args or None

        if not self.buffer.path:
            self.notify("save the file first before building", severity="warning")
            return

        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("cancelling previous build...", severity="warning")
            return

        self.buffer.save()

        engine = engine or cfg.get("compiler", "engine", "latexmk")
        auxDir = cfg.get("compiler", "aux_dir", ".aux")
        customCmd = cfg.get("compiler", "custom_cmd", "") or None
        autohide = cfg.get("compiler", "build_log_autohide", False)
        autoclose = cfg.get("compiler", "build_log_autoclose", False)

        if not customCmd and engine not in _compiler.PRESETS:
            self.notify(f"unknown engine '{engine}' - use :engines to list options", severity="warning")
            return

        panel = self.query_one(BuildPanel)
        panel.reset(engine, self.buffer.path)
        if not autohide:
            panel.display = True
            self.buildOpen = True

        self._buildStatus = "building ..."
        self.query_one(StatusBar).refresh()

        async def _run():
            def onLine(line, isErr):
                panel.appendLine(line, isErr)
            try:
                rc, _ = await _compiler.compile(
                    self.buffer.path,
                    engine=engine,
                    auxConfig=auxDir,
                    customCmd=customCmd,
                    onLine=onLine,
                )
                panel.setDone(rc)

                # parse log for errors / warnings
                lp = _compiler.logPath(self.buffer.path, engine, auxDir)
                panel.setErrors(_compiler.parse_log(lp))

                if rc == 0:
                    self._buildPrimed = True
                    self._buildStatus = "built"
                    self.notify(f"build succeeded ({engine})", timeout=3)
                    if autoclose and self.buildOpen:
                        panel.display = False
                        self.buildOpen = False
                else:
                    self._buildStatus = "failed"
                    self.notify(f"build failed (exit {rc})", severity="error", timeout=5)
            except asyncio.CancelledError:
                panel.appendLine("build cancelled", True)
                panel.setDone(1)
                self._buildStatus = ""
            except Exception as e:
                panel.appendLine(f"error: {e}", True)
                panel.setDone(1)
                self._buildStatus = "error"

            sb = self.query(StatusBar).first(None)
            if sb:
                sb.refresh()

        self._buildTask = asyncio.create_task(_run())

    @command(":clean", "remove aux dir files", section="Compiler")
    def _cmd_clean(self, args):
        if not self.buffer.path:
            self.notify("no file open", severity="warning")
            return
        auxDir = cfg.get("compiler", "aux_dir", ".aux")
        try:
            count = _compiler.cleanAuxDir(self.buffer.path, auxDir)
            self.notify(f"cleaned {count} file{'s' if count != 1 else ''} from {auxDir}")
        except Exception as e:
            self.notify(f"clean failed: {e}", severity="error")

    @command(":buildlog", "reopen last build panel", section="Compiler", aliases=[":buildpanel"])
    def _cmd_buildlog(self, args):
        from texitor.ui.buildpanel import BuildPanel
        panel = self.query_one(BuildPanel)
        if not panel._lines:
            self.notify("no build output yet - run :build first", severity="warning")
            return
        panel.display = True
        self.buildOpen = True

    @command(":buildstop", "cancel running build", section="Compiler", aliases=[":killbuild"])
    def _cmd_buildstop(self, args):
        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("build cancelled")
        else:
            self.notify("no build running", severity="warning")

    @command(":engines", "list available engines", section="Compiler", aliases=[":compilers"])
    def _cmd_listEngines(self, args):
        from texitor.ui.buildpanel import BuildPanel
        panel = self.query_one(BuildPanel)
        panel.reset("engines", "available engines")
        for name, desc in _compiler.ENGINE_DESCRIPTIONS.items():
            panel.appendLine(f"  {name:<14} {desc}", autoScroll=False)
        current = cfg.get("compiler", "engine", "latexmk")
        customCmd = cfg.get("compiler", "custom_cmd", "")
        panel.appendLine("", autoScroll=False)
        if customCmd:
            panel.appendLine("  custom_cmd is set - will be used instead of engine", autoScroll=False)
            panel.appendLine(f"  cmd: {customCmd}", autoScroll=False)
        else:
            panel.appendLine(f"  current engine: {current}  (compiler.engine)", autoScroll=False)
            panel.appendLine("  to use custom cmd: set compiler.custom_cmd", autoScroll=False)
        panel._scroll = 0
        panel.setDone(0)
        panel.display = True
        self.buildOpen = True
