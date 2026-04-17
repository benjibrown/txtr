---
title: Freeze Plugin Example
description: A concrete package-plugin example using the freeze CLI
---

The built-in `freeze` plugin is a concrete example of a package-style txtr plugin.

## What it does

- captures the current file with the `freeze` CLI
- if launched from Visual / Visual Line, it can use the selected line range
- writes output to a predictable image path unless you override it

## Why it is useful as an example

It exercises several parts of the plugin API at once:

- package plugin layout
- manifest metadata
- command parsing
- `ctx.selected_line_range`
- plugin config sections
- panel/log streaming
- subprocess execution

## Layout

```text
texitor/core/builtins/freeze/
  manifest.toml
  __init__.py
  helpers.py
```

## Config

```toml
[freeze]
executable = "freeze"
config = "full"
show_line_numbers = true
extra_args = ["--theme", "dracula"]
custom_command = ""
```

`config` may be a built-in freeze preset like `full` or a filesystem path like `~/.config/freeze/user.json`.

## Custom command placeholders

If `freeze.custom_command` is set, the plugin formats it with:

- `{FILE}`
- `{DIR}`
- `{STEM}`
- `{LINES}`
- `{LINES_ARG}`
- `{OUTPUT}`
- `{OUTPUT_ARG}`
- `{CONFIG}`
- `{CONFIG_ARG}`
- `{EXTRA_ARGS}`

That makes commands like this possible:

```toml
[freeze]
custom_command = "freeze {FILE} {CONFIG_ARG} {LINES_ARG} {OUTPUT_ARG} {EXTRA_ARGS}"
```

## Command behavior

- `:freeze` captures the whole file, or the current visual selection if one is active
- `:freeze full` forces a full-file capture
- `:freeze lines 10,20` captures an explicit line range

If the current buffer has unsaved changes, the plugin warns that freeze is using the last saved version on disk.
