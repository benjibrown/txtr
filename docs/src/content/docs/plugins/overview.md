---
title: Plugin System
description: Write, install, configure, and ship txtr plugins.
---

txtr plugins can add commands, statusbar segments, event hooks, panels, and custom UI widgets.

## Where plugins live

- **Built-in plugins** ship with txtr inside `texitor/core/builtins/`
- **User plugins** live in `~/.config/txtr/plugins/`

**txtr supports two plugin formats:**

### Single-file plugin

```text
~/.config/txtr/plugins/myplugin.py
```

```python
from texitor.core.plugins import PluginBase
from texitor.core.cmdregistry import registry

class MyPlugin(PluginBase):
    name = "myplugin"
    description = "demo plugin"
    version = "1.0.0"
    author = "you"
    commands = [
        (":myplugin hello <name>", "say hello"),
    ]

    def on_load(self, app):
        registry.register(
            ":myplugin hello <name>",
            "say hello",
            section="Plugin: myplugin",
            handler=self._cmd_hello,
        )

    def on_unload(self, app):
        registry.unregisterSection("Plugin: myplugin")

    def _cmd_hello(self, app, args):
        who = args.strip() or "world"
        self.notify(app, f"hello {who}")

plugin = MyPlugin
```

### Package plugin

```text
~/.config/txtr/plugins/myplugin/
  manifest.toml
  __init__.py
  helpers.py
```

`manifest.toml`:

```toml
name = "myplugin"
description = "demo package plugin"
version = "1.0.0"
author = "you"
entry = "__init__.py"

commands = [
  { syntax = ":myplugin hello <name>", description = "say hello" }
]
```

Package plugins use the manifest `name` as the canonical plugin name, even if the folder name differs.

## Plugin metadata

txtr reads these metadata fields from the plugin:

- `name`
- `description`
- `version`
- `author`
- `commands`

`commands` is optional but recommended. It lets `:plugin info <name>` show command docs even when the plugin is installed but not currently loaded.

## Hooks

All hooks are optional.

- `on_load(app)`
- `on_unload(app)`
- `on_save(app, path)`
- `on_cursor_move(app)`
- `on_mode_change(app, mode)`
- `on_build_done(app, rc)`
- `on_key(app, key, char)` — return `True` to consume the key
- `statusbar_segment(app)` — return `(text, color)` or `None`

## Config

Each plugin can read its own config section using `self.config(...)`.

```toml
[wordcount]
statusbar = true

[pomodoro]
default_minutes = 25
```

```python
class PomodoroPlugin(PluginBase):
    name = "pomodoro"

    def on_load(self, app):
        mins = self.config("default_minutes", 25)
        self.notify(app, f"default pomodoro = {mins}")
```

By default, `self.config("x")` reads from a section matching the plugin name, so `pomodoro` reads `[pomodoro]`.

You can also get the whole section:

```python
settings = self.config()
```

## Plugin context

Plugins can inspect editor state using `self.context(app)`.

```python
ctx = self.context(app)

ctx.file_path
ctx.cursor_row
ctx.cursor_col
ctx.mode
ctx.modified
ctx.current_line
ctx.line_count
ctx.selection_bounds
ctx.selected_line_range
ctx.selected_lines
ctx.selected_text
```

This is the preferred way to read editor state instead of scraping random app internals (understandbly tempting especially as the current level of context is pretty decent but not guaranteed to be perfect for every plugin's needs). 

`selected_line_range` is a 1-based inclusive `(start, end)` tuple, which is useful for tools like `freeze` that want a literal `--lines 12,20` style range.

## Built-in UI helpers

Plugins can use the same neutral info panel UI txtr uses internally:

```python
self.open_panel(app, "my plugin", [
    ("header", "Status"),
    ("row", "file", self.context(app).file_path),
    ("row", "mode", self.context(app).mode),
])

self.append_panel_text(app, "more log output...")
self.close_panel(app)
``````

Supported row shapes:

- `("header", "Section name")`
- `("row", "key", "value")`
- `("row", "key", "value", action)` for selectable rows
- `("text", "freeform wrapped text")`
- `("gap",)`

## Advanced UI

For more advanced plugins, you can mount your own Textual widgets:

```python
from textual.widget import Widget

widget = Widget()
self.mount_overlay(app, widget)
```

`mount_overlay()` mounts the widget on the overlay layer. Remove it later with:

```python
self.unmount_widget(app, widget)
```

This means plugins can use both:

- **simple built-in helpers** for quick panels
- **raw Textual widgets** for complex UI

## Commands

Plugin management commands:

- `:plugin list`
- `:plugin info <name>`
- `:plugin enable <name>`
- `:plugin disable <name>`
- `:plugin install <name>`
- `:plugin update [name]`
- `:plugin uninstall <name>`


## Lifecycle

### Install

` :plugin install <name> `

Downloads from the registry and enables the plugin.

### Enable

` :plugin enable <name> `

Loads a plugin that is already on disk and adds it to config.

### Disable

` :plugin disable <name> `

Unloads the plugin and removes it from config, but keeps files on disk.

### Uninstall

` :plugin uninstall <name> `

Disables the plugin and removes its file/folder from `~/.config/txtr/plugins/`.

### Auto-install

If a plugin is listed in:

```toml
[plugins]
enabled = ["wordcount"]
```

but is missing from disk, txtr can install it automatically on startup.

### Auto-update

```toml
[plugins]
auto_update = true
```

When enabled, txtr checks the registry on startup and updates installed user plugins whose version differs from the registry.

## Next reading

- [Plugin development](/plugins/development)
- [Freeze plugin example](/plugins/freeze-example)
- [Plugin config](/config/plugins)
