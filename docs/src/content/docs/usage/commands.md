---
title: Commands
description: "All : commands available in Command mode."
---

Press `:` in Normal mode to enter Command mode. Type a command and press `Enter`. Press `Escape` to cancel.

## File

txtr keeps the file commands intentionally small.

- `:w` saves the current buffer
- `:q` closes the current buffer, or quits txtr if it is the last one
- `:a` is a modifier for "all buffers"
- `!` forces the command
- you can stack modifiers together, so things like `:wa`, `:qa`, and `:wqa` work too

| Command | Description |
|---|---|
| `:w` | Save the current file |
| `:a` | Modifier for all buffers. Stack it with commands like `:w` or `:q` |
| `:q` | Close the current buffer, or quit txtr if it is the last one |
| `:q!` | Force-close the current buffer, or force-quit txtr if it is the last one |
| `:e <file>` | Open a file in a new buffer, or switch to it if it is already open |
| `:bn` | Switch to the next open buffer |
| `:bp` | Switch to the previous open buffer |
| `:buffers` / `:ls` | Show the open buffer list |
| `:explore` / `:ex` | Open the file explorer in the current file directory |

## View

| Command | Description |
|---|---|
| `:help` / `:h` | Open the help menu |
| `:snippets` / `:snips` | Open the Snippets tab in the help menu |
| `:config show` | Open the config panel |

## Config

| Command | Description |
|---|---|
| `:config get <key>` | Print the current value of a config key |
| `:config set <key> <value>` | Set a config value and persist it to disk |
| `:keybinds reload` | Reload `~/.config/txtr/keybinds.toml` without restarting |
| `:keybinds path` | Print the custom keybind file path |

Config keys use dot notation: `section.key`. The section prefix is optional for unambiguous keys.

```
:config get editor.tab_width
:config set editor.tab_width 2
:config set theme.name gruvbox
:config set editor.system_clipboard true
```

Changes take effect immediately for most editor settings. Theme changes require a restart.

Custom keybinds live in `~/.config/txtr/keybinds.toml`. See [Custom Keybinds](/usage/custom-keybinds).
