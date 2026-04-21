---
title: Plugin Configuration
description: Startup plugin config and per-plugin sections
---

## Plugin startup config

```toml
[plugins]
enabled = []
auto_update = false
```

- `enabled` is the list of plugin names txtr should load on startup
- `auto_update` makes txtr check the registry for updates on launch

## Per-plugin sections

Plugins can also read their own named config sections.

### Wordcount

```toml
[wordcount]
statusbar = true
count_math = false
```

### Freeze

```toml
[freeze]
executable = "freeze"
config = "full"
show_line_numbers = true
extra_args = ["--theme", "dracula"]
custom_command = ""
auto_copy = false
```

`freeze.config` can be either:

- a built-in freeze config name like `base`, `full`, or `user`
- or a real JSON config path like `~/.config/freeze/user.json`

The freeze plugin also supports custom command templating. See the [Freeze Example](/plugins/freeze-example) page for the placeholder list.

`wordcount.count_math = false` keeps the count focused on prose by ignoring math regions.

### Zathura

```toml```
[zathura]
executable = "zathura"
extra_args = []
auto_open_on_build = false
auto_sync_on_build = false
``````

Enable the plugin with:

```toml```
[plugins]
enabled = ["zathura"]
``````

Then use:

- `:pdf open` to launch the current file's PDF
- `:pdf` or `:pdf sync` to forward-search to the current cursor location

See [Zathura PDF Sync](/plugins/zathura) for the full workflow.

## Built-in overrides

Built-in plugins ship with txtr, but if a built-in plugin is also present in the registry you can update it into your user plugin directory. That user-installed copy becomes the override txtr uses.
