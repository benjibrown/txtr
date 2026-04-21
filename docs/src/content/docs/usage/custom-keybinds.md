---
title: Custom Keybinds
description: Override txtr keybinds with a dedicated keybinds.toml file.
---

txtr seeds a dedicated keybind file at:

```text
~/.config/txtr/keybinds.toml
```

This file contains **overrides only**. Defaults still exist unless you replace or disable them. Of course, you can also add new bindings that do not already exist.

## Quick examples

```toml
[normal]
"ctrl+s" = ":w"
"space b" = ":build"

[insert]
"ctrl+s" = ":w"
"ctrl+shift+v" = "system_paste"

[visual]
"?" = false
```

## Rules

1. Sections are: `[normal]`, `[insert]`, `[visual]`, `[visual_line]`, `[command]`, `[search]`
2. Values starting with `:` run a txtr command directly
3. Plain values call internal editor actions
4. Set a binding to `false` or `""` to disable it
5. Multi-key sequences use spaces, like `"g g"` or `"d d"`

## Action vs command bindings

Use an **action** when txtr already exposes the behavior internally:

```toml
[normal]
"ctrl+shift+c" = "system_copy"
"ctrl+shift+v" = "system_paste"
"ctrl+insert" = "system_copy"
"shift+insert" = "system_paste"
```

Use a **command binding** when you want to trigger a `:` command:

```toml
[normal]
"ctrl+s" = ":w"
"space l" = ":plugin list"
"space c" = ":config show"
```

## Available action names

Action bindings map straight onto txtr's internal `_action_<name>` handlers.

So if the action name is:

```text
system_paste
```

txtr looks for:

```text
_action_system_paste
```

and runs it.

Here are the current built-in action names you can bind to:

### Modes

```text
enter_normal
enter_insert
enter_insert_after
enter_insert_bol
enter_insert_eol
enter_visual
enter_visual_line
enter_command
enter_search
enter_search_back
```

### Movement

```text
cursor_left
cursor_right
cursor_up
cursor_down
line_start
line_end
goto_first_line
goto_last_line
word_forward
word_backward
word_end
scroll_half_down
scroll_half_up
```

### Search / command / help

```text
execute_command
execute_search
search_next
search_prev
open_help
close_help
accept_autocomplete
clear_tab_stops
```

### Editing

```text
backspace
newline
delete_char
delete_line
blackhole_delete_line
delete_word_before
delete_to_line_start
undo
redo
open_line_below
open_line_above
indent
dedent
replace_char
insert_tab
smart_tab
```

### Clipboard / paste / selections

```text
yank_line
paste_after
paste_before
system_copy
system_paste
yank_selection
delete_selection
```

If you bind to an action name that txtr does not recognise, it will warn with `unknown keybind action`.

## Disabling defaults

To remove a default mapping, set it to `false`:

```toml
[normal]
"?" = false
"ctrl+u" = false
```

## Sequence syntax

```toml
[normal]
"g g" = "goto_first_line"
"ctrl+shift+c" = "system_copy"
"left" = "cursor_left"
```

- named keys like `left`, `right`, `enter`, `escape`, `tab`, `backspace` use lowercase names
- modifier combos use forms like `ctrl+s` and `ctrl+shift+v`
- uppercase single keys like `G` or `V` are valid where case matters

## Reloading keybinds

You do not need to restart txtr after every edit.

```text
:keybinds reload
:keybinds path
```

`:keybinds path` prints the exact file path txtr is loading.

## Good starter setup

```toml
[normal]
"ctrl+s" = ":w"
"space b" = ":build"
"space w" = ":buildwatch"

[insert]
"ctrl+s" = ":w"
"ctrl+shift+v" = "system_paste"

[visual]
"ctrl+shift+c" = "system_copy"
"ctrl+insert" = "system_copy"
```


## Notes

- custom keybinds override defaults for the same sequence in the same mode
- command bindings run exactly the same command registry as typing `:` manually
- action bindings run the internal editor action directly, so names like `system_paste`, `cursor_left`, and `enter_insert` are valid bind targets
- clipboard shortcuts are direct system clipboard actions and do not depend on `editor.system_clipboard`
- many terminals intercept `ctrl+shift+c` / `ctrl+shift+v` before txtr sees them, so `ctrl+insert` / `shift+insert` are better terminal-friendly defaults
