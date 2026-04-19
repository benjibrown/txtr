---
title: Keybinds
description: Full default keybind reference for all modes.
---

## Normal mode

### Navigation

| Key | Action |
|---|---|
| `h` `j` `k` `l` | Left / down / up / right |
| `w` | Word forward |
| `b` | Word backward |
| `e` | Word end |
| `0` | Line start |
| `$` | Line end |
| `gg` | First line |
| `G` | Last line |
| `Ctrl+d` | Scroll half page down |
| `Ctrl+u` | Scroll half page up |
| Arrow keys | Also work for movement |

### Editing

| Key | Action |
|---|---|
| `dd` | Delete line (yanked to register) |
| `yy` | Yank line |
| `p` | Paste after cursor |
| `P` | Paste before cursor |
| `u` | Undo |
| `Ctrl+r` | Redo |
| `x` | Delete character under cursor |
| `r` | Replace character under cursor |
| `>` | Indent line |
| `<` | Dedent line |
| `Ctrl+Shift+c` / `Ctrl+Insert` | Copy current line to system clipboard |
| `Ctrl+Shift+v` / `Shift+Insert` | Paste from system clipboard |

### Mode switches

| Key | Mode |
|---|---|
| `i` | Insert before cursor |
| `I` | Insert at line start |
| `a` | Insert after cursor |
| `A` | Insert at line end |
| `o` | Open line below, insert |
| `O` | Open line above, insert |
| `v` | Visual |
| `V` | Visual Line |
| `:` | Command |
| `/` | Search |
| `?` | Help menu |
| `n` / `N` | Next / previous search match |

## Insert mode

| Key | Action |
|---|---|
| `Escape` / `Ctrl+[` | Return to Normal |
| `Tab` | Expand snippet or insert tab / jump to next tab stop |
| `Shift+Tab` | Clear remaining tab stops |
| `Ctrl+Space` | Accept autocomplete suggestion |
| `Up` / `Down` | Navigate autocomplete when open, otherwise move cursor |
| `Ctrl+w` | Delete word before cursor |
| `Ctrl+u` | Delete to line start |
| `Backspace` | Delete character (or whole tab chunk, or auto-pair) |
| `Ctrl+Shift+c` / `Ctrl+Insert` | Copy selection / line to system clipboard |
| `Ctrl+Shift+v` / `Shift+Insert` | Paste from system clipboard |
| Arrow keys | Move cursor |

## Visual / Visual Line mode

| Key | Action |
|---|---|
| `Escape` | Return to Normal |
| `y` | Yank selection |
| `d` | Delete selection |
| `>` | Indent selection |
| `<` | Dedent selection |
| `Ctrl+Shift+c` / `Ctrl+Insert` | Copy selection to system clipboard |
| `Ctrl+Shift+v` / `Shift+Insert` | Replace selection from system clipboard |
| Arrow keys | Extend selection |

## Command / Search mode

| Key | Action |
|---|---|
| `Escape` | Return to Normal |
| `Enter` | Run the command / search |
| `Ctrl+Shift+c` / `Ctrl+Insert` | Copy the current command/search text |
| `Ctrl+Shift+v` / `Shift+Insert` | Paste system clipboard text |

Note that many terminals swallow `Ctrl+Shift+c` / `Ctrl+Shift+v`, so txtr also supports `Ctrl+Insert` / `Shift+Insert`

## Customising keybinds

Custom keybinds are now documented on the dedicated [Custom Keybinds](/usage/custom-keybinds) page.
