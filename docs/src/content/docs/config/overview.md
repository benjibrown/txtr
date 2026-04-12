--- 
title: Configuration Overview 
description: Full config reference for ~/.config/txtr/config.toml 
--- 

Config lives at `~/.config/txtr/config.toml`. it is seeded from defaults on first run. Edit it directly or use `:config set` inside txtr. 

You can also view all your configuration options with `:config` inside txtr.

## Editor 

```toml
[editor]
tab_width = 4 
auto_pairs = true 
system_clipboard = false
blackhole_delete = false 
indent_guides = true 
wrap = true 
```
- `tab_width` sets the width of a tab character (in spaces)
- `auto_pairs` enables automatic insertion of matching pairs (e.g. parentheses, quotes)
- `system_clipboard` allows txtr to use the system clipboard for copy/paste operations instead of its internal yank register 
- `blackhole_delete` makes delete operations discard text instead of copying it to the yank register (delete instead of cut) - you may still use `_dd` to delete without copying 
- `indent_guides` shows vertical lines to indicate indentation levels 
- `wrap` enables line wrapping in the editor (`:set nowrap` to disable and `:set wrap` to enable)

## Theme 

```toml
[theme]
name = "catppuccin"
custom_path = ""
```
- `name` specifies the name of the color scheme to use - preinstalled themes include "catppuccin", "gruvbox", "nord", and "dracula". 
- `custom_path` allows you to specify a path to a custom theme file (e.g. `~/.config/txtr/themes/mytheme.toml`) - this will override the `name` field if provided.

See [Themes](/config/themes) for the custom theme format.

## Statusbar
```toml 
[statusbar] 
show_col = true 
show_mode = true 
```
- `show_col` toggles the display of the current column number in the statusbar 
- `show_mode` toggles the display of the current editor mode (e.g. NORMAL, INSERT) in the statusbar 


## Compiler
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
- `engine` specifies the LaTeX compilation engine to use (e.g. "latexmk", "pdflatex", "xelatex", "lualatex", "tectonic")
- `aux_dir` sets the directory where auxiliary files (e.g. .aux, .log) are stored during compilation (if supported by the engine)
- `custom_cmd` allows you to specify a custom compilation command (e.g. `latexmk -pdf -interaction=nonstopmode -synctex=1`) - this will override the `engine` and `aux_dir` fields if provided. 
- `autocompile` controls whether txtr automatically compiles your document on save - set to "save" to compile on every save (once you have manually compiled once), "always" to compile on every save without needing a manual compilation first, or "off" to disable autocompilation.
- `build_log_autohide` makes the build log remain hidden unless there is an error during compilation (in which case it will automatically show to display the error message)
- `build_log_autoclose` makes the build log automatically close when compilation finishes successfully
- `watch_interval` sets the interval (in seconds) at which txtr checks for changes to the source file when build watch mode is enabled - higher values may reduce CPU usage but make it less responsive to changes.

TODO - COMPILER SECTION - TO EXPLAIN IN DETAIL

## Citations 
```toml 
[citations] 
bib_files = []
```
- `bib_files` is a list of paths to .bib files that txtr will use for citation autocompletion and bibliography management. You can add multiple .bib files if needed (e.g. `["~/references.bib", "~/more_refs.bib"]`). This is supplementary to also scanning for .bib files in the current working directory. 

## Plugins 
```toml 
[plugins] 
enabled = []
auto_update = true
```
- `enabled` is a list of plugin names that you want to enable (e.g. `["wordcount"]`) - make sure to install the corresponding plugin files in `~/.config/txtr/plugins/` for them to work (unless built-in, in which case you just need to set config here to enable them)
- `auto_update` controls whether txtr automatically checks for updates to installed plugins on startup - if set to true, txtr will check for newer versions of your enabled plugins and update them if available. If set to false, txtr will not check for plugin updates automatically.

## Using :config set 

You can set values without leaving the editor (txtr will even reload them for you!) using `:config set` :
```
:config set editor.tab_width 2 
:config set theme.name gruvbox 
:config set statusbar.show_col false
```
