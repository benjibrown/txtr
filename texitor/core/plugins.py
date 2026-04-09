# FULL WIP - THIS IS ESSENTIALLY WHAT IT WILL LOOK LIKE WHEN DONE
# plugin system for txtr
#
# two plugin formats are supported: (if all goes to plan lol)
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
#           registry.register(":myplugin", "run my plugin", section="MyPlugin",)
#                             handler=lambda a, args: a.notify("hello from myplugin"))
#
#   plugin = MyPlugin
#
# hooks available (all optional):
#   on_load(app)				- called once when plugin is enabled
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
