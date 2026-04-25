from __future__ import annotations

import asyncio
from pathlib import Path

import texitor.core.compiler as _compiler
from texitor.core.cmdregistry import command
from texitor.core.config import config as cfg


class CompilerCommandsMixin:

    def _buildFailureNotice(self, engine, customCmd, rc, lines):
        # compiler UX time - please be less vague than "it died" lol
        msg = _compiler.failureSummary(engine, customCmd, lines)
        if msg:
            return msg
        return f"build failed (exit {rc})"

    def _cmd_buildSilent(self, engine=None, path=None):
        # same core build flow, just without popping the panel open every time
        from texitor.ui.buildpanel import BuildPanel
        from texitor.ui.statusbar import StatusBar
        from texitor.core.plugins import pluginLoader

        target_path = path or self.buffer.path
        if not target_path:
            return
        if self._buildTask and not self._buildTask.done():
            return

        buffer_idx = self._findBufferIndex(target_path)
        build_buffer = self.buffers[buffer_idx] if buffer_idx is not None else self.buffer
        if build_buffer.modified:
            build_buffer.save()

        engine = engine or cfg.get("compiler", "engine", "latexmk")
        auxDir = cfg.get("compiler", "aux_dir", ".aux")
        customCmd = cfg.get("compiler", "custom_cmd", "") or None
        preBuildCmd = cfg.get("compiler", "pre_build_cmd", "") or None
        postBuildCmd = cfg.get("compiler", "post_build_cmd", "") or None
        preBuildCmds = cfg.get("compiler", "pre_build_cmds", [])
        postBuildCmds = cfg.get("compiler", "post_build_cmds", [])

        if not customCmd and engine not in _compiler.PRESETS:
            self.notify(f"unknown engine '{engine}'", severity="warning")
            return

        panel = self.query_one(BuildPanel)
        panel.reset(engine, target_path)

        self._buildStatus = "building ..."
        sb = self.query(StatusBar).first(None)
        if sb:
            sb.refresh()

        async def _run():
            rc = 1
            lines = []

            def onLine(line, isErr):
                panel.appendLine(line, isErr)

            try:
                rc, lines = await _compiler.compile(
                    target_path,
                    engine=engine,
                    auxConfig=auxDir,
                    customCmd=customCmd,
                    onLine=onLine,
                    preBuildCmd=preBuildCmd,
                    postBuildCmd=postBuildCmd,
                    preBuildCmds=preBuildCmds,
                    postBuildCmds=postBuildCmds,
                )
                panel.setDone(rc)
                lp = _compiler.logPath(target_path, engine, auxDir)
                panel.setErrors(_compiler.parse_log(lp))

                if rc == 0:
                    build_buffer.build_primed = True
                    self._watchLastRevision[target_path] = build_buffer.revision
                    self.notify(f"build succeeded ({engine})", timeout=3)
                else:
                    self._closeOverlayPanels(except_name="build")
                    panel.display = True
                    self.buildOpen = True
                    self.notify(self._buildFailureNotice(engine, customCmd, rc, lines), severity="error", timeout=6)
            except asyncio.CancelledError:
                panel.appendLine("build cancelled", True)
                panel.setDone(1)
            except Exception as e:
                panel.appendLine(f"error: {e}", True)
                panel.setDone(1)

            pluginLoader.fireBuildDone(self, rc)

            if self._watchActive:
                self._buildStatus = "watching"
            else:
                self._buildStatus = "built" if build_buffer.build_primed else "failed"

            sb2 = self.query(StatusBar).first(None)
            if sb2:
                sb2.refresh()

        self._buildTask = asyncio.create_task(_run())

    @command(":build", "build with configured engine", section="Compiler", aliases=[":compile", ":b"])
    def _cmd_build(self, args):
        from texitor.ui.buildpanel import BuildPanel
        from texitor.ui.statusbar import StatusBar
        from texitor.core.plugins import pluginLoader

        engine = args or None

        if not self.buffer.path:
            self.notify("save the file first before building", severity="warning")
            return

        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("cancelling previous build...", severity="warning")
            return

        build_path = Path(self.buffer.path).expanduser()
        build_buffer = self.buffer
        if not build_path.exists():
            self.notify("save the file first before building", severity="warning")
            return
        if self.buffer.modified:
            self.notify("unsaved changes - building last saved version", severity="warning")

        engine = engine or cfg.get("compiler", "engine", "latexmk")
        auxDir = cfg.get("compiler", "aux_dir", ".aux")
        customCmd = cfg.get("compiler", "custom_cmd", "") or None
        preBuildCmd = cfg.get("compiler", "pre_build_cmd", "") or None
        postBuildCmd = cfg.get("compiler", "post_build_cmd", "") or None
        preBuildCmds = cfg.get("compiler", "pre_build_cmds", [])
        postBuildCmds = cfg.get("compiler", "post_build_cmds", [])
        autohide = cfg.get("compiler", "build_log_autohide", False)
        autoclose = cfg.get("compiler", "build_log_autoclose", False)

        if not customCmd and engine not in _compiler.PRESETS:
            self.notify(f"unknown engine '{engine}' - use :engines to list options", severity="warning")
            return

        panel = self.query_one(BuildPanel)
        panel.reset(engine, str(build_path))
        if not autohide:
            self._closeOverlayPanels(except_name="build")
            panel.display = True
            self.buildOpen = True

        self._buildStatus = "building ..."
        self.query_one(StatusBar).refresh()

        async def _run():
            rc = 1
            lines = []

            def onLine(line, isErr):
                panel.appendLine(line, isErr)

            try:
                rc, lines = await _compiler.compile(
                    str(build_path),
                    engine=engine,
                    auxConfig=auxDir,
                    customCmd=customCmd,
                    onLine=onLine,
                    preBuildCmd=preBuildCmd,
                    postBuildCmd=postBuildCmd,
                    preBuildCmds=preBuildCmds,
                    postBuildCmds=postBuildCmds,
                )
                panel.setDone(rc)

                lp = _compiler.logPath(str(build_path), engine, auxDir)
                panel.setErrors(_compiler.parse_log(lp))

                if rc == 0:
                    build_buffer.build_primed = True
                    self._buildStatus = "built"
                    self._watchLastRevision[str(build_path)] = build_buffer.revision
                    self.notify(f"build succeeded ({engine})", timeout=3)
                    if autoclose and self.buildOpen:
                        panel.display = False
                        self.buildOpen = False
                else:
                    self._buildStatus = "failed"
                    self._closeOverlayPanels(except_name="build")
                    panel.display = True
                    self.buildOpen = True
                    self.notify(self._buildFailureNotice(engine, customCmd, rc, lines), severity="error", timeout=6)
            except asyncio.CancelledError:
                panel.appendLine("build cancelled", True)
                panel.setDone(1)
                self._buildStatus = ""
            except Exception as e:
                panel.appendLine(f"error: {e}", True)
                panel.setDone(1)
                self._buildStatus = "error"
                self._closeOverlayPanels(except_name="build")
                panel.display = True
                self.buildOpen = True

            if self._watchActive:
                self._buildStatus = "watching"

            pluginLoader.fireBuildDone(self, rc)

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
        self._closeOverlayPanels(except_name="build")
        panel.display = True
        self.buildOpen = True

    @command(":buildstop", "cancel running build", section="Compiler", aliases=[":killbuild"])
    def _cmd_buildstop(self, args):
        if self._buildTask and not self._buildTask.done():
            self._buildTask.cancel()
            self.notify("build cancelled")
        else:
            self.notify("no build running", severity="warning")

    @command(":buildwatch", "toggle continuous build on every edit", section="Compiler", aliases=[":bw"])
    def _cmd_buildwatch(self, args):
        from texitor.ui.statusbar import StatusBar

        if self._watchActive:
            self._watchActive = False
            if self._watchTask and not self._watchTask.done():
                self._watchTask.cancel()
                self._watchTask = None
            # wherever u see this its just making sure the watch buffer path doesnt go feral
            self._watchBufferPath = None
            self._buildStatus = ""
            sb = self.query(StatusBar).first(None)
            if sb:
                sb.refresh()
            self.notify("buildwatch stopped")
            return

        if not self.buffer.path:
            self.notify("save the file first", severity="warning")
            return

        self._watchActive = True
        self._watchBufferPath = self.buffer.path
        self._watchLastRevision[self.buffer.path] = self.buffer.revision
        self._buildStatus = "watching"
        sb = self.query(StatusBar).first(None)
        if sb:
            sb.refresh()
        delay = cfg.get("compiler", "watch_interval", 1.5)
        self._startWatchLoop()
        self.notify(f"buildwatch active for {Path(self.buffer.path).name} - builds {delay}s after each edit - :bw to stop")

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
        self._closeOverlayPanels(except_name="build")
        panel.display = True
        self.buildOpen = True
