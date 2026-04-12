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

    def _loadedKey(self, name: str):
        if name in self._loaded:
            return name
        for key, instance in self._loaded.items():
            if getattr(instance, "_txtr_source_name", "") == name:
                return key
        return None

    def loadAll(self, app, enabled: list):
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        for name in enabled:
            self.load(app, name, notify_error=True)

    def load(self, app, name: str, notify_error=False):
        # name here is the filesystem name (dir name or .py stem)
        # canonical name comes from manifest.toml `name` field (package)
        # or the `name` class attribute (single file)
        if self._loadedKey(name):
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
        instance._txtr_source_name = name
        instance._txtr_source_path = str(path)
        instance._txtr_is_package = is_pkg

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
        key = self._loadedKey(name)
        if key is None:
            return False
        instance = self._loaded.pop(key)
        try:
            instance.on_unload(app)
        except Exception:
            pass
        return True

    def unloadAll(self, app):
        for name in list(self._loaded.keys()):
            self.unload(app, name)

    def isLoaded(self, name: str) -> bool:
        return self._loadedKey(name) is not None

    def loaded(self) -> list[str]:
        return list(self._loaded.keys())

    def get(self, name: str):
        key = self._loadedKey(name)
        return self._loaded.get(key) if key else None

    def installedMetadata(self) -> list[dict]:
        PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        found = {}
        for path, is_pkg in _scanPluginCandidates(PLUGIN_DIR):
            meta = _metadataForPath(path, is_pkg)
            found[meta["name"]] = meta
        for path, is_pkg in _scanPluginCandidates(_builtinDir()):
            meta = _metadataForPath(path, is_pkg)
            found.setdefault(meta["name"], meta)
        return [found[name] for name in sorted(found)]

    # event dispatch - call each loaded plugin's hook, swallow exceptions per-plugin

    def fireSave(self, app, path):
        for p in self._loaded.values():
            try:
                p.on_save(app, path)
            except Exception:
                pass

    def fireCursorMove(self, app):
        for p in self._loaded.values():
            try:
                p.on_cursor_move(app)
            except Exception:
                pass

    def fireModeChange(self, app, mode):
        for p in self._loaded.values():
            try:
                p.on_mode_change(app, mode)
            except Exception:
                pass

    def fireBuildDone(self, app, rc):
        for p in self._loaded.values():
            try:
                p.on_build_done(app, rc)
            except Exception:
                pass

    def fireKey(self, app, key, char) -> bool:
        for p in self._loaded.values():
            try:
                if p.on_key(app, key, char):
                    return True
            except Exception:
                pass
        return False

    def statusbarSegments(self, app) -> list:
        segments = []
        for p in self._loaded.values():
            try:
                seg = p.statusbar_segment(app)
                if seg:
                    segments.append(seg)
            except Exception:
                pass
        return segments

    def availableOnDisk(self) -> list[str]:
        return [meta["name"] for meta in self.installedMetadata()]


def _resolvePlugin(name: str, search_dirs: list):
    for d in search_dirs:
        if d is None:
            continue
        pkg = d / name
        if pkg.is_dir() and any((pkg / ep).exists() for ep in _ENTRY_POINTS):
            return pkg, True
        single = d / f"{name}.py"
        if single.exists():
            return single, False
        for path, is_pkg in _scanPluginCandidates(d):
            meta = _metadataForPath(path, is_pkg)
            if meta["name"] == name:
                return path, is_pkg
    return None, False


def _loadClass(path: Path, name: str, is_pkg=False):
    if is_pkg:
        manifest = _readManifest(path)
        entry_name = manifest.get("entry", "") if manifest else ""
        entry = None
        candidates = [entry_name] + list(_ENTRY_POINTS) if entry_name else list(_ENTRY_POINTS)
        for ep in candidates:
            candidate = path / ep
            if candidate.exists():
                entry = candidate
                break
        if entry is None:
            raise ValueError(f"no entry point found in {path}")

        parent = str(path.parent)
        if parent not in sys.path:
            sys.path.insert(0, parent)

        mod_name = f"txtr_plugin_{name}"
        spec = importlib.util.spec_from_file_location(
            mod_name,
            entry,
            submodule_search_locations=[str(path)],
        )
    else:
        manifest = None
        spec = importlib.util.spec_from_file_location(f"txtr_plugin_{name}", path)

    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"txtr_plugin_{name}"] = mod
    spec.loader.exec_module(mod)

    cls = getattr(mod, "plugin", None)
    if cls is None:
        for attr in vars(mod).values():
            if isinstance(attr, type) and issubclass(attr, PluginBase) and attr is not PluginBase:
                cls = attr
                break
    if cls is None:
        raise ValueError(f"no PluginBase subclass found in {path}")
    return cls, manifest


def _readManifest(pkg_dir: Path):
    m = pkg_dir / "manifest.toml"
    if not m.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(m.read_text())
    except Exception:
        return {}


def readMetadata(name: str) -> dict:
    # read plugin metadata from disk without executing the plugin
    # for packages: reads manifest.toml
    # for single files: scans class attributes with ast (safe, no imports run)
    path, is_pkg = _resolvePlugin(name, [PLUGIN_DIR, _builtinDir()])
    if path is None:
        return {}

    if is_pkg:
        m = _readManifest(path)
        return {
            "name": m.get("name", name),
            "description": m.get("description", ""),
            "version": m.get("version", ""),
            "author": m.get("author", ""),
            "type": "package",
            "path": str(path),
        }

    # single file - parse with ast to extract class attributes safely
    import ast
    try:
        src = path.read_text(errors="replace")
        tree = ast.parse(src)
    except Exception:
        return {"name": name, "type": "single file", "path": str(path)}

    meta = {"name": name, "description": "", "version": "", "author": "", "type": "single file", "path": str(path)}
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue
            for target in stmt.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id in ("name", "description", "version", "author"):
                    val = stmt.value
                    if isinstance(val, ast.Constant) and isinstance(val.value, str):
                        if not meta[target.id] or target.id == "name":
                            meta[target.id] = val.value
    return meta


def _builtinDir():
    return Path(__file__).parent / "builtins"


def _builtinPath(name: str):
    here = _builtinDir()
    pkg = here / name
    if pkg.is_dir() and any((pkg / ep).exists() for ep in _ENTRY_POINTS):
        return pkg
    single = here / f"{name}.py"
    return single if single.exists() else None


def _builtinNames() -> list[str]:
    here = _builtinDir()
    if not here.exists():
        return []
    names = set()
    for p in here.glob("*.py"):
        if not p.name.startswith("_"):
            names.add(p.stem)
    for d in here.iterdir():
        if d.is_dir() and not d.name.startswith("_") and any(
            (d / ep).exists() for ep in _ENTRY_POINTS
        ):
            names.add(d.name)
    return sorted(names)


pluginLoader = PluginLoader()
