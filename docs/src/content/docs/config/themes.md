--- 
title: Themes 
description: Switching and creating themes in txtr.
--- 

txtr ships with 4 built-in themes and supports fully custom themes via a TOML file.
## Built-in themes 

| Name | Description |
| --- | --- |
| `catppuccin` | Catppuccin Mocha - the default. |
| `gruvbox` | Gruvbox Dark. |
| `nord` | Nord. |
| `dracula` | Dracula. |

Switch theme:

```
:config set theme.name gruvbox 
```

Restart txtr for the change to take effect. 

## Custom themes 

In order to set a custom theme for use in txtr, you need to create a seperate TOML file with the theme configuration and define the path to it in the config.

```toml 
[theme]
....
custom_path = "/path/to/theme.toml"
```

If you have a `custom_path` defined, the built-in themes will be ignored and only the custom theme will be used.

Of course, you can also use txtr's config manager to set the `theme.custom_path` value:

```
:config set theme.custom_path /path/to/theme.toml
```

## Custom theme format 

The custom theme file is a TOML file with the following format:

```toml

bg           = "#1a1b26"   # main editor background
bg_alt       = "#16161e"   # statusbar / panel header background
bg_popup     = "#1f2335"   # dropdown and popup surface
cursor_line  = "#1e2030"   # current line subtle highlight
bg_sel       = "#2d3f76"   # visual selection background
bg_search    = "#ffc777"   # search match highlight background
border       = "#3b4261"   # borders and separators

fg           = "#c0caf5"   # default text
fg_dim       = "#565f89"   # very muted (placeholder, disabled)
fg_muted     = "#545c7e"   # muted (line numbers, comments)
fg_sub       = "#9aa5ce"   # subtle secondary text

accent       = "#7aa2f7"   # primary accent (normal mode, keybinds)
accent2      = "#bb9af7"   # secondary accent (visual mode, section headers)
green        = "#9ece6a"   # insert mode, LaTeX env names
yellow       = "#e0af68"   # warnings
orange       = "#ff9e64"   # math regions
red          = "#f7768e"   # errors, command mode
```

All 17 fields are required for a valid theme. You can use the built-in themes as a reference for creating your own custom themes.

If any of the fields are missing or invalid, txtr will fall back to the default `catppuccin` theme and shows a startup notification explaining what went wrong.

Made a custom theme you want to share? Open an issue or a PR on the GitHub repo!
