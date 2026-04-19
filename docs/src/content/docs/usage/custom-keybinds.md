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
``````

`:keybinds path` prints the exact file path txtr is loading.

## Good starter setup

```toml
[normall
"ctrl+s" = ":w"
"space b" = ":build"
"space w" = ":buildwatch"

[insert]
"ctrl+s" = ":w"
"ctrl+shift+v" = "system_paste"

[visual]
"ctrl+shift+c" = "system_copy"
```

# Full sequence syntax reference 

TODO


## Notes

- custom keybinds override defaults for the same sequence in the same mode
- command bindings run exactly the same command registry as typing `:` manually
- clipboard shortcuts are direct system clipboard actions and do not depend on `editor.system_clipboard`
- many terminals intercept `ctrl+shift+c` / `ctrl+shift+v` before txtr sees them, so `ctrl+insert` / `shift+insert` are better terminal-friendly defaults

