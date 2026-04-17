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
```

### Freeze

```toml
[freeze]
executable = "freeze"
config = "full"
show_line_numbers = true
extra_args = ["--theme", "dracula"]
custom_command = ""
```

`freeze.config` can be either:

- a built-in freeze config name like `base`, `full`, or `user`
- or a real JSON config path like `~/.config/freeze/user.json`

The freeze plugin also supports custom command templating. See the [Freeze Example](/plugins/freeze-example) page for the placeholder list.

## Built-in overrides

Built-in plugins ship with txtr, but if a built-in plugin is also present in the registry you can update it into your user plugin directory. That user-installed copy becomes the override txtr uses.
