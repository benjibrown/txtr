from __future__ import annotations

import asyncio

from texitor.core.cmdregistry import command
from texitor.core.config import config as cfg


class PluginCommandsMixin:

    async def _pluginFetchRegistry(self, registry_url):
        import json
        import urllib.request

        try:
            with urllib.request.urlopen(registry_url, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            self.notify(f"could not fetch registry: {e}", severity="error")
            return None

    def _pluginInfoRows(self, meta, loaded, plugin_cmds, config_options=None):
        from texitor.ui.plugininfo import pluginInfoRows

        return pluginInfoRows(meta, loaded, plugin_cmds, config_options=config_options)

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

            if inst:
                meta = {
                    "name": inst.name or arg,
                    "description": inst.description or "",
                    "version": inst.version or "",
                    "author": inst.author or "",
                    "type": "package" if getattr(inst, "_txtr_is_package", False) else "single file",
                    "path": getattr(inst, "_txtr_source_path", ""),
                    "commands": getattr(inst, "commands", []),
                    "config_options": getattr(inst, "config_options", []),
                }
            else:
                meta = readMetadata(arg)

            canonical = meta.get("name") or arg
            plugin_section = f"Plugin: {canonical}"
            plugin_cmds = next((cmds for section, cmds in _reg.sections() if section == plugin_section), [])
            if not plugin_cmds:
                plugin_cmds = meta.get("commands", [])

            self._openInfoPanel(
                f"plugin: {canonical}",
                self._pluginInfoRows(meta, loaded, plugin_cmds, config_options=meta.get("config_options", [])),
            )

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
                self._pluginRememberKnown(canonical)
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
            self._pluginRememberKnown(canonical)
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
            self.notify("unknown plugin action - use list/info/enable/disable/install/update/uninstall", severity="warning")

    async def _plugin_install(self, name: str, registry_url: str, plugin_dir):
        from texitor.core.plugins import readMetadata

        meta = readMetadata(name)
        if meta:
            path = meta.get("path", "")
            canonical = meta.get("name") or name
            if path.startswith(str(plugin_dir)):
                self.notify(f"plugin '{canonical}' is already installed - use :plugin update {canonical}", severity="warning")
            else:
                self.notify(f"plugin '{canonical}' is already available as a built-in plugin - use :plugin enable {canonical} or :plugin update {canonical}", severity="warning")
            return
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

        user_installed = [
            meta
            for meta in pluginLoader.installedMetadata()
            if meta.get("path", "").startswith(str(plugin_dir))
        ]
        installed = user_installed
        target_meta = None
        if name:
            target_meta = next((meta for meta in pluginLoader.installedMetadata() if meta["name"] == name), None)
            if not target_meta:
                self.notify(f"plugin '{name}' is not installed", severity="warning")
                return
            installed = [target_meta]
            if not data.get(target_meta["name"]):
                self.notify(f"plugin '{name}' is not in the registry", severity="warning")
                return
        elif not user_installed:
            self.notify("no installed user plugins to update", severity="warning")
            return

        updates = []
        for meta in installed:
            entry = data.get(meta["name"])
            if not entry:
                continue
            target_version = entry.get("version", "")
            is_user_plugin = meta.get("path", "").startswith(str(plugin_dir))
            if name and not is_user_plugin:
                updates.append((meta, entry, True))
                continue
            if target_version and target_version != meta.get("version", ""):
                updates.append((meta, entry, False))

        if not updates:
            self.notify("plugins already up to date")
            return

        self._openInfoPanel(
            "plugin update",
            [("header", "Updating plugins"), ("text", f"{len(updates)} plugin(s) need updating")],
            footer="  q close",
        )

        updated = []
        for meta, entry, force_override in updates:
            was_loaded = pluginLoader.isLoaded(meta["name"])
            ok, canonical = await self._pluginInstallFromEntry(
                meta["name"],
                entry,
                plugin_dir,
                load_after=was_loaded,
                update_loaded=was_loaded,
                status_label="refreshing" if force_override else "updating",
            )
            if ok:
                updated.append((canonical, meta.get("version", "?"), entry.get("version", "?"), force_override))

        if updated:
            self._appendInfoPanelText("")
            self._appendInfoPanelStatus("done.", "success")
            for canonical, old, new, force_override in updated:
                if force_override and old == new:
                    self._appendInfoPanelStatus(f"{canonical}: installed registry override ({new})", "success")
                else:
                    self._appendInfoPanelStatus(f"{canonical}: {old} -> {new}", "success")
            self.notify(f"updated {len(updated)} plugin(s)")

    async def _pluginInstallFromEntry(self, name, entry, plugin_dir, load_after, update_loaded, status_label):
        import io
        import shutil
        import tempfile
        import urllib.request
        import zipfile
        from pathlib import Path
        from texitor.core.plugins import pluginLoader, readMetadata

        plugin_dir.mkdir(parents=True, exist_ok=True)
        was_loaded = pluginLoader.isLoaded(name)
        url = entry.get("url", "")
        if not url:
            self._appendInfoPanelStatus(f"{name}: registry entry has no url", "error")
            return False, name

        pkg_type = entry.get("type", "single")
        self._appendInfoPanelStatus(f"{status_label} {name} ({pkg_type})", "info")

        if pkg_type == "git":
            dest = plugin_dir / name
            if dest.exists():
                rc = await self._pluginRunProcess(["git", "-C", str(dest), "pull"], cwd=None)
            else:
                rc = await self._pluginRunProcess(["git", "clone", "--depth=1", url, str(dest)], cwd=None)
            if rc != 0:
                self._appendInfoPanelStatus(f"{name}: git command failed", "error")
                return False, name

        elif pkg_type == "package":
            self._appendInfoPanelStatus(f"downloading {url}", "command")
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    raw = r.read()
            except Exception as e:
                self._appendInfoPanelStatus(f"download failed: {e}", "error")
                return False, name
            try:
                with tempfile.TemporaryDirectory() as td:
                    tmp_root = Path(td)
                    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
                        members = [m for m in zf.namelist() if not m.startswith("__MACOSX")]
                        zf.extractall(tmp_root, members=members)
                    subdir = (entry.get("subdir", "") or "").strip().strip("/")
                    source = tmp_root / subdir if subdir else None
                    if source is None or not source.exists():
                        candidates = [
                            p for p in tmp_root.rglob("*")
                            if p.is_dir() and ((p / "manifest.toml").exists() or any((p / ep).exists() for ep in ("__init__.py", "plugin.py", "main.py")))
                        ]
                        source = candidates[0] if len(candidates) == 1 else None
                    if source is None or not source.exists():
                        self._appendInfoPanelStatus("extract failed: could not find package root in archive", "error")
                        return False, name
                    dest = plugin_dir / name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(source, dest)
                    self._appendInfoPanelStatus(f"extracted package to {dest}", "success")
            except Exception as e:
                self._appendInfoPanelStatus(f"extract failed: {e}", "error")
                return False, name

        else:
            self._appendInfoPanelStatus(f"downloading {url}", "command")
            try:
                with urllib.request.urlopen(url, timeout=15) as r:
                    raw = r.read()
            except Exception as e:
                self._appendInfoPanelStatus(f"download failed: {e}", "error")
                return False, name
            dest = plugin_dir / f"{name}.py"
            dest.write_bytes(raw)
            self._appendInfoPanelStatus(f"wrote {dest}", "success")

        meta = readMetadata(name)
        canonical = meta.get("name") or name
        enabled = cfg.get("plugins", "enabled", [])
        should_sync_config = load_after or name in enabled or canonical in enabled

        if update_loaded or (load_after and was_loaded):
            pluginLoader.unload(self, name)

        if load_after:
            ok = pluginLoader.load(self, canonical, notify_error=True)
            if not ok:
                self._appendInfoPanelStatus(f"{canonical}: failed to load after {status_label}", "error")
                return False, canonical

        if should_sync_config:
            self._pluginEnableName(name, canonical)

        self._appendInfoPanelStatus(f"{canonical}: {status_label} complete", "success")
        return True, canonical

    async def _pluginRunProcess(self, args, cwd=None):
        # plugin installer output is noisy as hell so this keeps it in one place
        self._appendInfoPanelStatus("$ " + " ".join(args), "command")
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode(errors="replace").rstrip()
            if text:
                level = "error" if "error" in text.lower() or "failed" in text.lower() else "info"
                self._appendInfoPanelStatus(text, level)
        return await proc.wait()

    def _pluginEnableName(self, old_name, canonical):
        enabled = [name for name in cfg.get("plugins", "enabled", []) if name != old_name and name != canonical]
        enabled.append(canonical)
        cfg.set("plugins", "enabled", enabled)
        self._pluginRememberKnown(canonical)

    def _pluginRemoveEnabledNames(self, *names):
        enabled = [name for name in cfg.get("plugins", "enabled", []) if name not in names]
        cfg.set("plugins", "enabled", enabled)

    def _pluginRememberKnown(self, *names):
        known = set(cfg.get("plugins", "known", []))
        for name in names:
            if name:
                known.add(name)
        cfg.set("plugins", "known", sorted(known))

    def _plugin_uninstall(self, name, plugin_dir):
        import shutil
        from pathlib import Path
        from texitor.core.plugins import pluginLoader, readMetadata

        meta = readMetadata(name)
        if not meta:
            self.notify(f"plugin '{name}' is not installed", severity="warning")
            return

        path = Path(meta.get("path", ""))
        if not path.exists():
            self.notify(f"plugin '{name}' is not installed", severity="warning")
            return
        if not str(path).startswith(str(plugin_dir)):
            self.notify(f"plugin '{name}' is built-in and cannot be uninstalled", severity="warning")
            return

        canonical = meta.get("name") or name
        pluginLoader.unload(self, canonical)
        self._pluginRemoveEnabledNames(name, canonical)
        known = [item for item in cfg.get("plugins", "known", []) if item not in (name, canonical)]
        cfg.set("plugins", "known", known)

        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        except Exception as e:
            self.notify(f"could not uninstall '{canonical}': {e}", severity="error")
            return

        self.notify(f"plugin '{canonical}' uninstalled")

    async def _startupPlugins(self):
        from texitor.core.plugins import pluginLoader, PLUGIN_DIR, REGISTRY_URL, readMetadata

        enabled = cfg.get("plugins", "enabled", [])
        auto_update = cfg.get("plugins", "auto_update", False)
        missing = [name for name in enabled if not readMetadata(name)]
        registry = None

        if missing or auto_update:
            registry = await self._pluginFetchRegistry(REGISTRY_URL)

        if missing and registry:
            self._openInfoPanel(
                "plugin startup",
                [("header", "Installing missing plugins"), ("text", f"{len(missing)} plugin(s) missing from disk")],
                footer="  q close",
            )
            for name in missing:
                entry = registry.get(name)
                if not entry:
                    self._appendInfoPanelText(f"{name}: not found in registry")
                    continue
                await self._pluginInstallFromEntry(
                    name,
                    entry,
                    PLUGIN_DIR,
                    load_after=False,
                    update_loaded=False,
                    status_label="installing",
                )
            self._appendInfoPanelText("startup install pass complete")

        if auto_update and registry:
            installed = [
                meta
                for meta in pluginLoader.installedMetadata()
                if meta.get("path", "").startswith(str(PLUGIN_DIR))
            ]
            outdated = []
            for meta in installed:
                entry = registry.get(meta["name"])
                if not entry:
                    continue
                target_version = entry.get("version", "")
                if target_version and target_version != meta.get("version", ""):
                    outdated.append((meta, entry))

            if outdated:
                if not self.infoOpen:
                    self._openInfoPanel(
                        "plugin startup",
                        [("header", "Updating plugins"), ("text", f"{len(outdated)} plugin(s) need updates")],
                        footer="  q close",
                    )
                else:
                    self._appendInfoPanelText("")
                    self._appendInfoPanelText(f"updating {len(outdated)} plugin(s)")
                for meta, entry in outdated:
                    await self._pluginInstallFromEntry(
                        meta["name"],
                        entry,
                        PLUGIN_DIR,
                        load_after=False,
                        update_loaded=False,
                        status_label="updating",
                    )
                self._appendInfoPanelText("startup update pass complete")

        if enabled:
            pluginLoader.loadAll(self, cfg.get("plugins", "enabled", []))

        self._notifyNewPlugins()
