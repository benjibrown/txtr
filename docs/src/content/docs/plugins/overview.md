--- 
title: Plugin System 
description: Write, install, configure, and ship txtr plugins.
--- 

txtr plugins can add commands, statusbar segments, event hooks, panels, and custom UI elements. 

## Where plugins live 

- **Built-in plugins** ship with txtr inside the source code - at `texitor/core/builtins/`.
- **User plugins** live in `~/.config/txtr/plugins/`.

txtr supports two plugin formats:

### Single-file plugin
