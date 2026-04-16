---
title: Plugin Development
description: Build plugins for txtr
---

This page is about writing plugins, not just installing them.

## Choose a format

Use a **single-file plugin** when the plugin is small and self-contained.

Use a **package plugin** when you need:

- helper modules
- bundled assets
- more than one command or helper file
- a cleaner structure for publishing

The built-in `freeze` plugin is a package plugin and is a good reference example.

## Minimal workflow

1. subclass `PluginBase`
2. set metadata like `name`, `description`, `version`, `author`
3. register commands in `on_load`
4. unregister your command section in `on_unload`

## Recommended metadata

- `name`
- `description`
- `version`
- `author`
- `commands`

`commands` is worth filling out even for installed-but-not-loaded plugins because txtr can show it in `:plugin info`.

## Command patterns

The simplest plugin command looks like this:

```python
registry.register()
    ":myplugin <args>",
    "run my plugin",
    section="Plugin: myplugin",
    aliases=[":myplugin"],
    handler=self._cmd_myplugin,
)
```

Use the `<args>` form when you want prefix-style matching. Add an alias without `<args>` if the command should also work with no arguments.

## Reading editor state

Prefer:

```python
ctx = self.context(app)
````

over scraping random app internals directly ( if something is missing, submit an issue or PR to add it to the context! ).

Useful fields include:

- `ctx.file_path`
- `ctx.mode`
- `ctx.modified`
- `ctx.selection_bounds`
- `ctx.selected_line_range`
- `ctx.selected_lines`
- `ctx.selected_text`

If a command is launched from Visual or Visual Line mode, txtr preserves that selection context during command dispatch so plugins can still inspect it.

## Config helpers

Plugins can read their own config section with:

```python
self.config("key", default)
self.config()
```

If your plugin is named `freeze`, the default section is `[freeze]`.

## UI helpers

For quick UI:

```python
self.open_panel(app, "title", [])
    ("header", "Section"),
    ("row", "key", "value"),
    ("text", "streamed output"),
])
```

For richer UI, mount raw Textual widgets:

```python
widget = MyWidget()
self.mount_overlay(app, widget)
```

## Publishing and registry entries

Registry entries can point at:

- a raw single-file plugin
- a git repo
- a package zip

Package entries can also target a subdirectory inside an archive, which is useful when the plugin lives inside a larger repository.

## Built-in override behavior

Built-in plugins are not locked forever. If a built-in plugin is also in the registry, `:plugin update <name>` can install a user override copy into `~/.config/txtr/plugins/`.

That means you can:

- ship built-in reference plugins with txtr
- still update them independently later

## Example plugin to study

See [Freeze Example](/plugins/freeze-example) for a complete package-plugin example that uses:

- plugin config
- command parsing
- visual selection line ranges
- subprocess execution
- streamed panel output

