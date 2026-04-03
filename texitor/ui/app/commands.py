# the commands mixing - methdos + tab stop actions!! 

from __future__ import annotations 
import asyncio 

import texitor.core.compiler as _compiler 
from texitor.core.config import config as cfg 

class CommandsMixin:
    # TODO - inegrate this into cmd registry so its not a massive if statement
    def _action_execute_command(self):
        from texitor.ui.helpmenu import HelpMenu 
        from texitor.ui.configpanel import ConfigPanel 
        from texitor.ui.buildpanel import BuildPanel 
        from texitor.ui.editor import EditorWidget 

        cmd = self.cmd_input.strip()
        self._action_enter_normal()

        if cmd == "w":
            self._cmd_write()
        elif cmd == "q":
            self._cmd_quit()
        elif cmd in ("wq", "x"):
            self._cmd_write()
            self.exit()
        elif cmd == "q!":
            self.exit()
        elif cmd in ("help", "h"):
            self._action_open_help()
        elif cmd in ("snippets", "snips"):
            self.helpOpen = True 
            menu = self.query_one(HelpMenu)
            menu.open()
            menu.nextTab()
        elif cmd.startswith("e "):
            path = cmd[2:].strip()
            if path:
                self.buffer.load(path)
                self._refresh_all()
        elif cmd.startswith("w "):
            path = cmd[2:].strip()
            if path:
                self.buffer.save(path)
        elif cmd in ("config show", "config", "cfg"):
            self._cmd_configShow()
        elif cmd in ("config set", "config get", "cfg set", "cfg get"):
            self.notify(
                f":{cmd} <section.key> <value>" if cmd == "config set" else f":{cmd} <section.key>",
                severity="warning",
            )
        elif cmd.startswith("config set"):
            self._cmd_configSet(cmd[len("config set"):].strip())
        elif cmd.startswith("config get"):
            self._cmd_configGet(cmd[len("config get"):].strip())
        elif cmd in ("build", "compile", "b"):
            self._cmd_build()
        elif cmd.startswith("build ") or cmd.startswith("compile "):
            engine = cmd.split(None, 1)[1].strip()
            self._cmd_build(engine=engine)
        elif cmd == "clean":
            self._cmd_clean()
        elif cmd in ("buildlog", "buildpanel"):
            self._cmd_buildlog()
        elif cmd in ("buildstop", "killbuild"):
            self._cmd_buildstop()
        elif cmd in ("engines", "compilers"):
            self._cmd_listEngines()
        elif cmd == "set wrap":
            cfg.set("editor", "wrap", True)
            self.query_one(EditorWidget).rebuildVisualLines()
            self._refresh_all()
            self.notify("wrap on")
        elif cmd == "set nowrap":
            cfg.set("editor", "wrap", False)
            self.query_one(EditorWidget).rebuildVisualLines()
            self._refresh_all()
            self.notify("wrap off")
        else:
            self.notify(f"unknown command: {cmd}", severity="warning")


    def _cmd_configShow(self):
        from texitor.ui.configpanel import ConfigPanel  
        self.configOpen = True 
        self.query_one(ConfigPanel).open()

    def _cmd_configSet(self, args):
        from texitor.ui.app import _coerceValue, _resolveConfigKey
        parts = args.split(None, 1)
        if len(parts) != 2:
            self.notify(":config set <section.key> <value>", severity="warning")
            return
        dotKey, rawVal = parts 
        section, key = _resolveConfigKey(dotKey)
        if section is None:
            self.notify(f"config: unknown key: '{dotKey}'", severity="warning")
            return 
        value = _coerceValue(rawVal) 
        cfg.set(section, key, value)
        self.notify(f"config: {section}.{key} = {value}")

    def _cmd_configGet(self, dotKey):
        from texitor.ui.app import _resolveConfigKey 
        if not dotKey:
            self.notify(":config get <section.key>", severity="warning")
            return
        section, key = _resolveConfigKey(dotKey)
        if section is None:
            self.notify(f"config: unknown key: '{dotKey}'", severity="warning")
            return
        val = cfg.get(section, key)
        if val is None:
            self.notify(f"config: {section}.{key} not set", severity="warning")
        else:
            self.notify(f"{section}.{key} = {val}")

    # file cmds 

    def _cmd_write(self):
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
            self._cmd_build()

    def _cmd_quit(self):
        if self.buffer.modified:
            self.notify("unsaved changes - use :q! to force quit", severity="warning")
            return 
        self.exit()

    # build cmds 

    def _cmd_build(self, engine=None): 
        from texitor.ui.buildpanel import BuildPanel 
        from texitor.ui.statusbar import StatusBar

        if not self.buffer.path:
            self.notify("save the file first before building", severity="warning")
            return

        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("canceling previous build...", severity="warning")
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


    def _cmd_clean(self):
        if not self.buffer.path:
            self.notify("no file open", severity="warning") 
            return 
        auxDir = cfg.get("compiler", "aux_dir", ".aux")
        try:
            count = _compiler.cleanAuxDir(self.buffer.path, auxDir)
            self.notify(f"cleaned {count} file{'s' if count != 1 else ''} from {auxDir}")
        except Exception as e:
            self.notify(f"error during clean: {e}", severity="error")

    def _cmd_buildlog(self):
        from texitor.ui.buildpanel import BuildPanel 
        panel = self.query_one(BuildPanel)
        if not panel._lines:
            self.notify("no build output yet - run :build first", severity="warning")
            return
        panel.display = True 
        self.buildOpen = True 
    
    def _cmd_buildstop(self):
        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("build cancelled")
        else:
            self.notify("no build running", severity="warning")

    def _cmd_listEngines(self):
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
