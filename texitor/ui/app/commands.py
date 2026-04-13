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
    _SECTION_ORDER = ["File", "View", "Config", "Compiler", "Plugins"]

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

    def _openInfoPanel(self, title, rows, footer=None):
        from texitor.ui.infopanel import InfoPanel
        self.infoOpen = True
        self.query_one(InfoPanel).open(title, rows, footer=footer)

    def _setInfoPanelRows(self, rows, footer=None):
        from texitor.ui.infopanel import InfoPanel
        self.infoOpen = True
        self.query_one(InfoPanel).setRows(rows, footer=footer)

    def _appendInfoPanelText(self, text, autoScroll=True):
        from texitor.ui.infopanel import InfoPanel
        self.infoOpen = True
        self.query_one(InfoPanel).appendText(text, autoScroll=autoScroll)

    async def _pluginFetchRegistry(self, registry_url):
        import json
        import urllib.request

        try:
            with urllib.request.urlopen(registry_url, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            self.notify(f"could not fetch registry: {e}", severity="error")
            return None

    def _pluginInfoRows(self, meta, loaded, plugin_cmds):
        rows = [
            ("row", "name", meta.get("name") or "(unknown)"),
            ("row", "version", meta.get("version") or "(unknown)"),
            ("row", "author", meta.get("author") or "(unknown)"),
            ("row", "description", meta.get("description") or "(none)"),
            ("row", "type", meta.get("type", "single file")),
            ("row", "status", "loaded" if loaded else "not loaded"),
            ("row", "path", meta.get("path") or "not found on disk"),
        ]
        if plugin_cmds:
            rows.append(("gap",))
            rows.append(("header", "Commands"))
            for cmd, desc in plugin_cmds:
                rows.append(("row", cmd, desc))
        return rows

        
    # file commands

    @command(":w", "save file", section="File")
    def _cmd_write(self, args):
        from texitor.core.plugins import pluginLoader
        if args:
            self.buffer.save(args)
            self.notify(f"saved {args}")
            pluginLoader.fireSave(self, args)
            return
        if not self.buffer.path:
            self.notify("no file name - use :w <filename>", severity="warning")
            return
        self.buffer.save()
        self.notify(f"saved {self.buffer.path}")
        pluginLoader.fireSave(self, self.buffer.path)
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
            self._loadBibsForFile(args)
            self._refresh_all()
        else:
            self.notify(":e <filename>", severity="warning")

    @command(":bib", "reload .bib files from current file's directory", section="File")
    def _cmd_bib(self, args):
        path = self.buffer.path
        if not path:
            self.notify("no file open", severity="warning")
            return
        self._loadBibsForFile(path, fromcmd=True)


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

    def _cmd_buildSilent(self, engine=None):
        # like _cmd_build but never opens the build panel (used by buildwatch)
        from texitor.ui.buildpanel import BuildPanel
        from texitor.ui.statusbar import StatusBar
        from texitor.core.plugins import pluginLoader

        if not self.buffer.path:
            return
        if self._buildTask and not self._buildTask.done():
            return

        self.buffer.save()

        engine = engine or cfg.get("compiler", "engine", "latexmk")
        auxDir = cfg.get("compiler", "aux_dir", ".aux")
        customCmd = cfg.get("compiler", "custom_cmd", "") or None

        if not customCmd and engine not in _compiler.PRESETS:
            self.notify(f"unknown engine '{engine}'", severity="warning")
            return

        panel = self.query_one(BuildPanel)
        panel.reset(engine, self.buffer.path)

        self._buildStatus = "building ..."
        sb = self.query(StatusBar).first(None)
        if sb:
            sb.refresh()

        async def _run():
            rc = 1
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
                lp = _compiler.logPath(self.buffer.path, engine, auxDir)
                panel.setErrors(_compiler.parse_log(lp))

                if rc == 0:
                    self._buildPrimed = True
                    self.notify(f"build succeeded ({engine})", timeout=3)
                else:
                    panel.display = True
                    self.buildOpen = True
                    self.notify(f"build failed (exit {rc})", severity="error", timeout=5)
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
                self._buildStatus = "built" if self._buildPrimed else "failed"

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
            rc = 1
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
        self._buildStatus = "watching"
        sb = self.query(StatusBar).first(None)
        if sb:
            sb.refresh()
        delay = cfg.get("compiler", "watch_interval", 1.5)
        self._startWatchLoop()
        self.notify(f"buildwatch active - builds {delay}s after each edit - :bw to stop")

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

    @command(":plugin", "manage plugins - list / info / enable / disable / install / update / uninstall", section="Plugins")
    def _cmd_plugin(self, args):
        from texitor.core.plugins import pluginLoader, PLUGIN_DIR, REGISTRY_URL, readMetadata
        from texitor.core.cmdregistry import registry as _reg

        sub = (args or "").strip()
        parts = sub.split(None, 1)
        action = parts[0].lower() if parts else "list"
        arg = parts[1].strip() if len(parts) > 1 else ""

        if action == "list":
            rows = []
            installed = pluginLoader.installedMetadata()
            loaded = set(pluginLoader.loaded())

            rows.append(("header", "Loaded plugins"))
            if loaded:
                for meta in installed:
                    if meta["name"] not in loaded:
                        continue
                    right = f"v{meta.get('version') or '?'}"
                    if meta.get("author"):
                        right += f"  by {meta['author']}"
                    rows.append(("row", meta["name"], right, ("plugin-info", meta["name"])))
            else:
                rows.append(("row", "(none)", "use :plugin enable <name> to load one"))

            not_loaded = [meta for meta in installed if meta["name"] not in loaded]
            if not_loaded:
                rows.append(("gap",))
                rows.append(("header", "Installed but not loaded"))
                for meta in not_loaded:
                    rows.append(("row", meta["name"], meta.get("type", "plugin"), ("plugin-info", meta["name"])))

            rows.append(("gap",))
            rows.append(("header", "Plugin directory"))
            rows.append(("text", str(PLUGIN_DIR)))
            self._openInfoPanel("plugins", rows)

        elif action == "info":
            if not arg:
                self.notify("usage: :plugin info <name>", severity="warning")
                return

            inst = pluginLoader.get(arg)
            loaded = inst is not None

            # get metadata from live instance if loaded, else read from disk
            if inst:
                meta = {
                    "name": inst.name or arg,
                    "description": inst.description or "",
                    "version": inst.version or "",
                    "author": inst.author or "",
                    "type": "package" if getattr(inst, "_txtr_is_package", False) else "single file",
                    "path": getattr(inst, "_txtr_source_path", ""),
                    "commands": getattr(inst, "commands", []),
                }
            else:
                meta = readMetadata(arg)

            canonical = meta.get("name") or arg
            plugin_section = f"Plugin: {canonical}"
            plugin_cmds = next((cmds for section, cmds in _reg.sections() if section == plugin_section), [])
            if not plugin_cmds:
                plugin_cmds = meta.get("commands", [])

            self._openInfoPanel(f"plugin: {canonical}", self._pluginInfoRows(meta, loaded, plugin_cmds))

        elif action == "enable":
            if not arg:
                self.notify("usage: :plugin enable <name>", severity="warning")
                return
            enabled = cfg.get("plugins", "enabled", [])
            meta = readMetadata(arg)
            canonical = meta.get("name") or arg
            if pluginLoader.isLoaded(arg) and canonical in enabled:
                self.notify(f"plugin '{arg}' is already enabled", severity="warning")
                return
            if not meta and arg not in pluginLoader.availableOnDisk():
                self.notify(f"plugin '{arg}' is not installed", severity="warning")
                return
            ok = pluginLoader.load(self, arg, notify_error=True)
            if ok:
                inst = pluginLoader.get(arg)
                canonical = inst.name if inst and inst.name else arg
                self._pluginEnableName(arg, canonical)
                self.notify(f"plugin '{canonical}' enabled")

        elif action == "disable":
            if not arg:
                self.notify("usage: :plugin disable <name>", severity="warning")
                return
            enabled = cfg.get("plugins", "enabled", [])
            inst = pluginLoader.get(arg)
            canonical = inst.name if inst and inst.name else arg
            if canonical not in enabled and not pluginLoader.isLoaded(arg):
                self.notify(f"plugin '{arg}' is already disabled", severity="warning")
                return
            ok = pluginLoader.unload(self, arg)
            self._pluginRemoveEnabledNames(arg, canonical)
            if ok or canonical not in enabled:
                self.notify(f"plugin '{canonical}' disabled")
            else:
                self.notify(f"plugin '{arg}' is not loaded", severity="warning")

        elif action == "install":
            if not arg:
                self.notify("usage: :plugin install <name>", severity="warning")
                return
            asyncio.create_task(self._plugin_install(arg, REGISTRY_URL, PLUGIN_DIR))

        elif action == "update":
            asyncio.create_task(self._plugin_update(arg, REGISTRY_URL, PLUGIN_DIR))

        elif action == "uninstall":
            if not arg:
                self.notify("usage: :plugin uninstall <name>", severity="warning")
                return
            self._plugin_uninstall(arg, PLUGIN_DIR)

        else:
            self.notify(f"unknown plugin action '{action}' - use list/info/enable/disable/install/update/uninstall", severity="warning")

    async def _plugin_install(self, name: str, registry_url: str, plugin_dir):
        data = await self._pluginFetchRegistry(registry_url)
        if not data:
            return
        entry = data.get(name)
        if not entry:
            self.notify(f"'{name}' not found in registry", severity="warning")
            return

        self._openInfoPanel(
            f"plugin install: {name}",
            [("header", "Installing plugin"), ("text", f"registry entry found for {name}")],
            footer="  q close",
        )
        ok, canonical = await self._pluginInstallFromEntry(
            name,
            entry,
            plugin_dir,
            load_after=True,
            update_loaded=False,
            status_label="installing",
        )
        if ok:
            self._appendInfoPanelText("")
            self._appendInfoPanelText(f"{canonical}: installation finished")
            self.notify(f"plugin '{canonical}' installed and enabled")

    async def _plugin_update(self, name: str, registry_url: str, plugin_dir):
        from texitor.core.plugins import pluginLoader

        data = await self._pluginFetchRegistry(registry_url)
        if not data:
            return

        installed = [
            meta
            for meta in pluginLoader.installedMetadata()
            if meta.get("path", "").startswith(str(plugin_dir))
        ]
        if name:
            installed = [meta for meta in installed if meta["name"] == name]
            if not installed:
                self.notify(f"plugin '{name}' is not installed", severity="warning")
                return
            if installed and not data.get(installed[0]["name"]):
                self.notify(f"plugin '{name}' is not in the registry", severity="warning")
                return
        elif not installed:
            self.notify("no installed user plugins to update", severity="warning")
            return

        outdated = []
        for meta in installed:
            entry = data.get(meta["name"])
            if not entry:
                continue
            target_version = entry.get("version", "")
            if target_version and target_version != meta.get("version", ""):
                outdated.append((meta, entry))

        if not outdated:
            self.notify("plugins already up to date")
            return

        self._openInfoPanel(
            "plugin update",
            [("header", "Updating plugins"), ("text", f"{len(outdated)} plugin(s) need updating")],
            footer="  q close",
        )

        updated = []
        for meta, entry in outdated:
            was_loaded = pluginLoader.isLoaded(meta["name"])
            ok, canonical = await self._pluginInstallFromEntry(
                meta["name"],
                entry,
                plugin_dir,
                load_after=was_loaded,
                update_loaded=was_loaded,
                status_label="updating",
            )
		# TODO - finish this lol
        url = entry.get("url", "")
        if not url:
            self.notify(f"registry entry for '{name}' has no url", severity="error")
            return

        pkg_type = entry.get("type", "single")

        if pkg_type == "git":
            dest = plugin_dir / name
            if dest.exists():
                # already cloned - pull instead
                self.notify(f"updating '{name}' (git pull)...")
                proc = await asyncio.create_subprocess_exec(
                    "git", "-C", str(dest), "pull",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    self.notify(f"git pull failed: {stderr.decode()[:120]}", severity="error")
                    return
            else:
                self.notify(f"cloning '{name}'...")
                proc = await asyncio.create_subprocess_exec(
                    "git", "clone", "--depth=1", url, str(dest),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                _, stderr = await proc.communicate()
                if proc.returncode != 0:
                    self.notify(f"git clone failed: {stderr.decode()[:120]}", severity="error")
                    return

        elif pkg_type == "package":
            # zip containing the plugin directory
            import zipfile, io, urllib.request
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    raw = r.read()
            except Exception as e:
                self.notify(f"download failed: {e}", severity="error")
                return
            try:
                with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                    members = [m for m in zf.namelist() if not m.startswith("__MACOSX")]
                    zf.extractall(plugin_dir, members=members)
            except Exception as e:
                self.notify(f"failed to extract package: {e}", severity="error")
                return

        else:
            # single .py file
            import urllib.request
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    raw = r.read()
            except Exception as e:
                self.notify(f"download failed: {e}", severity="error")
                return
            dest = plugin_dir / f"{name}.py"
            dest.write_bytes(raw)

        ok = pluginLoader.load(self, name, notify_error=True)
        if ok:
            inst = pluginLoader.get(name)
            canonical = inst.name if inst and inst.name else name
            cfg.append("plugins", "enabled", canonical)
            self.notify(f"plugin '{canonical}' installed and enabled")
