--- 
title: Snippets Overview
description: How the txtr snippet engine works
--- 

txtr ships with a LaTeX snippet library and a simple engine for expanding them. Snippets are defined in`~/.config/txtr/snippets.toml` and can be edited freely - the file is yours to customize.

## Trigger types

There are two ways that a snippet in txtr can fire.

### Auto-expand

The snippet fires as you type, the moment the trigger sequence is completed. No extra keypress is needed.

Auto-expand is used for symbol sequences that are unambiguous in a LaTeX document - things like `//` for `\frac{}{}` or `@a` or `\alpha`. These are unlikely to appear in normal text, so false positives are rare.

If an auto-expand fires unexpectedly, press `Backspace` to undo the expansion.

### Tab-triggered

Type the trigger word, then press `Tab`. Used for alphabetic triggers like `int`, `sum`, or `begin` - words that could appear in normal text and should not fire automatically. 

## Tab Stops

Most snippets include tab stops: `${1}`, `${2}`, etc. After a snippet expands, your cursor is placed at the first tab stop. Press `Tab` to jump to the next one, and so on. Press `Shift+Tab` to clear all remaining tab stops and exit snippet navigation.

Tab stops also allow for placeholder text. For example, a snippet define with the tab stop `${1:placeholder}` will expand with "placeholder" as the default text in that position. You can overwrite it by typing or jump past it by hitting `Tab`.

## Customisation 

### Snippet file location
```
~/.config/txtr/snippets.toml
```

The file is seeded from bundled defaults on the first run. Edit it directly to add, change or remove snippets. The format is documented in the file itself.

### Adding a custom snippet 

Open `~/.config/txtr/snippets.toml` and add a new entry under the appropriate section. For example, to add a new auto-expand snippet for `\sqrt{}`:

```toml
[triggers.mysnip]
trigger = "ms"
body = "\\mycommand{${1}}"
auto_expand = false 
```
- `trigger` - the text that actually triggers the snippet 
- body - the expansion (use `${1}`, `${2}`, etc. for tab stops)
- `auto_expand` - set to `true` for auto-expanding snippets, `false` requires `Tab`

The above snippet will expand `ms` to `\mycommand{}` when you press `Tab` after typing `ms`. The cursor will be placed inside the braces, ready for you to type whatever your heart desires.

Whenever you edit your snippets, restart txtr to pick up the changes. Happy snipping!
