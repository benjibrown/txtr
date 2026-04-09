# plugin system for txtr
#
# two plugin formats are supported:
#
# SINGLE FILE  ~/.config/txtr/plugins/myplugin.py
#   simple, one file, no dependencies
#
# PACKAGE  ~/.config/txtr/plugins/myplugin/
#   directory-based, can have helper modules, assets, etc.
#   entry point is resolved in order: __init__.py -> plugin.py -> main.py
#   optional manifest.toml in the package root:
#       name = "myplugin"
#       description = "does something"
#       version = "1.0.0"
#       author = "you"
#       entry = "plugin.py"   # override entry point
#
# package layout example:
#   myplugin/
#       __init__.py     <- entry point (or plugin.py / main.py)
#       helpers.py      <- any extra modules, importable as myplugin.helpers
#       manifest.toml   <- optional metadata
#
# example minimal plugin (single file or __init__.py):
#
#   from texitor.core.plugins import PluginBase
#   from texitor.core.cmdregistry import registry
#
#   class MyPlugin(PluginBase):
#       name = "myplugin"
#       description = "does something cool"
#
#       def on_load(self, app):
#           registry.register(":myplugin", "run my plugin", section="MyPlugin",
#                             handler=lambda a, args: a.notify("hello from myplugin"))
#
#   plugin = MyPlugin   # <- loader looks for this export
#
# hooks available (all optional):
#   on_load(app)              - called once when plugin is enabled

#   on_unload(app)            - called when plugin is disabled or app exits
#   on_save(app, path)        - called after every file save
#   on_cursor_move(app)       - called after cursor position changes
#   on_mode_change(app, mode) - called when editor mode changes
#   on_build_done(app, rc)    - called after a build (rc=0 is success)
#   on_key(app, key, char)    - called on every keypress; return True to consume
#   statusbar_segment(app)    - return (text, color) tuple or None
#
# commands:
#   :plugin list              - show all known/loaded plugins
#   :plugin enable <name>     - enable a plugin (adds to config)
#   :plugin disable <name>    - disable a plugin (removes from config)
#   :plugin install <name>    - download a plugin from the registry

from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None


PLUGIN_DIR = Path.home() / ".config" / "txtr" / "plugins"
REGISTRY_URL = "https://raw.githubusercontent.com/benjibrown/txtr/main/plugin-registry.json"

_ENTRY_POINTS = ("__init__.py", "plugin.py", "main.py")


class PluginBase:
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    author: str = ""

    def on_load(self, app):
        pass

    def on_unload(self, app):
        pass

    def on_save(self, app, path):
        pass

    def on_cursor_move(self, app):
        pass

    def on_mode_change(self, app, mode):
        pass

    def on_build_done(self, app, rc):
        pass

    def on_key(self, app, key, char):
        return False

    def statusbar_segment(self, app):
        return None


class PluginLoader:

    def __init__(self):
        self._loaded: dict[str, PluginBase] = {}

    def loadAll(self, app, enabled: list):
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        for name in enabled:
            self.load(app, name, notify_error=True)

    def load(self, app, name: str, notify_error=False):
        # name here is the filesystem name (dir name or .py stem)
        # canonical name comes from manifest.toml `name` field (package)
        # or the `name` class attribute (single file)
        if name in self._loaded:
            return True

        path, is_pkg = _resolvePlugin(name, [PLUGIN_DIR, _builtinDir()])

        if path is None:
            if notify_error:
                app.notify(f"plugin '{name}' not found in {PLUGIN_DIR}", severity="warning")
            return False

        try:
            cls, manifest = _loadClass(path, name, is_pkg)
        except Exception as e:
            if notify_error:
                app.notify(f"plugin '{name}' failed to load: {e}", severity="error")
            return False

        instance = cls()

        # manifest fields always win over class attributes
        if manifest:
            for k in ("name", "description", "version", "author"):
              if k in manifest and manifest[k]:
                    setattr(instance, k, manifest[k])

        # canonical name: manifest/class `name`, falling back to filesystem name
        canonical = instance.name or name

        # already loaded under its canonical name (e.g. dir name differs from manifest name)
        if canonical in self._loaded:
            return True

        try:
            instance.on_load(app)
        except Exception as e:
            if notify_error:
                app.notify(f"plugin '{canonical}' on_load error: {e}", severity="error")
            return False

        self._loaded[canonical] = instance
        return True

    def unload(self, app, name: str):
        # accepts either canonical name or filesystem name
        instance = self._loaded.pop(name, None)
        if instance is None:
            # try matching by filesystem name against stored canonical names
            canonical = next((k for k, v in self._loaded.items() if k == name), None)
            if canonical:
                instance = self._loaded.pop(canonical)
            else:
                return False
        try:
            instance.on_unload(app)
        except Exception:
            pass
        return True

    def unloadAll(self, app):
        for name in list(self._loaded.keys()):
            self.unload(app, name)

    def isLoaded(self, name: str) -> bool:
        return name in self._loaded

