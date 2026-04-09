---
title: Commands
description: "All : commands available in Command mode."
---

Press `:` in Normal mode to enter Command mode. Type a command and press `Enter`. Press `Escape` to cancel.

## File

| Command | Description |
|---|---|
| `:w` | Save the current file |
| `:q` | Quit |
| `:wq` | Save and quit |
| `:e <file>` | Open a file |

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

Config keys use dot notation: `section.key`. The section prefix is optional for unambiguous keys.

``````
:config get editor.tab_width
:config set editor.tab_width 2
:config set theme.name gruvbox
:config set editor.system_clipboard true
``````

Changes take effect immediately for most editor settings. Theme changes require a restart.

