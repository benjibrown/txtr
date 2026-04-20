# plugin system for txtr
# just removed all the long ass comments in here that are in docs now

from __future__ import annotations
import ast
import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

from texitor.core.config import config as cfg
from texitor.core.modes import Mode

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


@dataclass
class PluginContext:
    file_path: str = ""
    cursor_row: int = 0
    cursor_col: int = 0
    mode: str = "NORMAL"
    modified: bool = False
    current_line: str = ""
    line_count: int = 0
    selection_bounds: tuple | None = None
    selected_line_range: tuple | None = None
    selected_lines: list[str] = field(default_factory=list)
    selected_text: str = ""


class PluginBase:
    name: str = ""
    description: str = ""
    version: str = "0.1.0"
    author: str = ""
    commands: list = []
    config_options: list = []
    config_section: str = ""

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

    def config(self, key=None, default=None, section=None):
        sec = section or self.config_section or self.name
        if not sec:
            return {} if key is None else default
        if key is None:
            return cfg.getSection(sec)
        return cfg.get(sec, key, default)

    def context(self, app):
        return pluginContext(app)

    def notify(self, app, message, severity="information", timeout=3):
        app.notify(message, severity=severity, timeout=timeout)

    def open_panel(self, app, title, rows, footer=None):
        app.plugin_open_panel(title, rows, footer=footer)

    def set_panel_rows(self, app, rows, footer=None):
        app.plugin_set_panel_rows(rows, footer=footer)

    def append_panel_text(self, app, text, autoScroll=True):
        app.plugin_append_panel_text(text, autoScroll=autoScroll)

    def close_panel(self, app):
        app.plugin_close_panel()

    def mount_overlay(self, app, widget):
        return app.plugin_mount_overlay(widget)

    def unmount_widget(self, app, widget):
        return app.plugin_unmount_widget(widget)


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
    return _metadataForPath(path, is_pkg)


def pluginContext(app, mode_override=None) -> PluginContext:
    cached = getattr(app, "_commandContext", None)
    if cached is not None and mode_override is None:
        return cached

    buf = app.buffer
    source_mode = mode_override or getattr(app, "_commandSourceMode", None) or app.msm.mode
    bounds = app._selection_bounds() if hasattr(app, "_selection_bounds") else None
    selected_line_range = None
    selected_lines = []
    selected_text = ""

    if source_mode is Mode.VISUAL_LINE and app.visual_anchor is not None:
        r0 = min(app.visual_anchor[0], buf.cursor_row)
        r1 = max(app.visual_anchor[0], buf.cursor_row)
        selected_line_range = (r0 + 1, r1 + 1)
        selected_lines = list(buf.lines[r0 : r1 + 1])
        selected_text = "\n".join(selected_lines)
    elif bounds is not None:
        r0, c0, r1, c1 = bounds
        selected_line_range = (r0 + 1, r1 + 1)
        if r0 == r1:
            selected_lines = [buf.lines[r0][c0 : c1 + 1]]
        else:
            selected_lines = (
                [buf.lines[r0][c0:]]
                + list(buf.lines[r0 + 1 : r1])
                + [buf.lines[r1][: c1 + 1]]
            )
        selected_text = "\n".join(selected_lines)

    return PluginContext(
        file_path=buf.path or "",
        cursor_row=buf.cursor_row,
        cursor_col=buf.cursor_col,
        mode=source_mode.name,
        modified=buf.modified,
        current_line=buf.current_line,
        line_count=buf.line_count,
        selection_bounds=bounds,
        selected_line_range=selected_line_range,
        selected_lines=selected_lines,
        selected_text=selected_text,
    )


def _scanPluginCandidates(base: Path):
    if not base.exists():
        return []
    out = []
    for p in base.glob("*.py"):
        if not p.name.startswith("_"):
            out.append((p, False))
    for d in base.iterdir():
        if d.is_dir() and not d.name.startswith("_") and any((d / ep).exists() for ep in _ENTRY_POINTS):
            out.append((d, True))
    return out


def _metadataForPath(path: Path, is_pkg: bool) -> dict:
    name = path.name if is_pkg else path.stem

    if is_pkg:
        m = _readManifest(path)
        return {
            "name": m.get("name", name),
            "description": m.get("description", ""),
            "version": m.get("version", ""),
            "author": m.get("author", ""),
            "commands": _parseManifestCommands(m),
            "config_options": _parseManifestConfigOptions(m),
            "type": "package",
            "path": str(path),
        }

    # single file - parse with ast to extract class attributes safely
    try:
        src = path.read_text(errors="replace")
        tree = ast.parse(src)
    except Exception:
        return {"name": name, "description": "", "version": "", "author": "", "commands": [], "config_options": [], "type": "single file", "path": str(path)}

    meta = {"name": name, "description": "", "version": "", "author": "", "commands": [], "config_options": [], "type": "single file", "path": str(path)}
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
                elif target.id == "commands":
                    parsed = _parseCommandList(stmt.value)
                    if parsed:
                        meta["commands"] = parsed
                elif target.id == "config_options":
                    parsed = _parseConfigOptions(stmt.value)
                    if parsed:
                        meta["config_options"] = parsed
    return meta


def _parseManifestCommands(manifest: dict) -> list:
    commands = manifest.get("commands", [])
    if not isinstance(commands, list):
        return []
    out = []
    for item in commands:
        if isinstance(item, dict):
            syntax = item.get("syntax", "")
            description = item.get("description", "")
            if syntax and description:
                out.append((syntax, description))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            syntax = str(item[0]).strip()
            description = str(item[1]).strip()
            if syntax and description:
                out.append((syntax, description))
    return out


def _parseManifestConfigOptions(manifest: dict) -> list:
    return _normalizeConfigOptions(manifest.get("config_options", []))


def _parseCommandList(node) -> list: 
    try:
        value = ast.literal_eval(node)
    except Exception:
        return []
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if isinstance(item, dict):
            syntax = str(item.get("syntax", "")).strip()
            description = str(item.get("description", "")).strip()
            if syntax and description:
                out.append((syntax, description))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            syntax = str(item[0]).strip()
            description = str(item[1]).strip()
            if syntax and description:
                out.append((syntax, description))
    return out


def _parseConfigOptions(node) -> list:
    try:
        value = ast.literal_eval(node)
    except Exception:
        return []
    return _normalizeConfigOptions(value)


def _normalizeConfigOptions(value) -> list:
    if not isinstance(value, list):
        return []
    out = []
    for item in value:
        if not isinstance(item, dict):
            continue
        key = str(item.get("key", "")).strip()
        if not key:
            continue
        out.append({
            "key": key,
            "default": item.get("default", ""),
            "description": str(item.get("description", "")).strip(),
        })
    return out


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
    return [meta["name"] for meta in ( _metadataForPath(path, is_pkg) for path, is_pkg in _scanPluginCandidates(_builtinDir()) )]


pluginLoader = PluginLoader()
