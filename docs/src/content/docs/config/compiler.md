---
title: Compiler Configuration
description: Compiler and build-log options
---

## Compiler section

```toml
[compiler]
engine = "latexmk"
aux_dir = ".aux"
custom_cmd = ""
autocompile = "off"
build_log_autohide = false
build_log_autoclose = false
watch_interval = 5
```

## Keys

- `engine` chooses the built-in compiler preset
- txtr's built-in presets also enable SyncTeX output so PDF forward-search plugins can work
- `aux_dir` controls where aux and log files go when the engine supports it
- `custom_cmd` overrides the preset completely
- `autocompile` supports:
  - `"off"` - requires manual compilation
  - `"save"` - compiles on file save but must be initiated with `:build` at least once
  - `"always"` - compiles on file save without needing to initiate with `:build`
- `build_log_autohide` keeps the log closed unless a build fails
- `build_log_autoclose` closes the build log after successful builds
- `watch_interval` controls `:buildwatch` debounce timing

If you use `custom_cmd` and want PDF sync features, include your own SyncTeX flag in that command.

## Common setups

### Standard LaTeXmk

```toml
[compiler]
engine = "latexmk"
aux_dir = ".aux"
autocompile = "save"
```

### Tectonic

```toml
[compiler]
engine = "tectonic"
autocompile = "off"
```

### Fully custom command

```toml
[compiler]
custom_cmd = "latexmk -pdf -interaction=nonstopmode -synctex=1 {file}"
```
