---
title: Zathura PDF Viewer
description: Open PDFs in Zathura and jump to the current source location with SyncTeX.
---

The built-in `zathura` plugin gives txtr a proper PDF-viewer system without trying to render PDFs inside the TUI.

It is focused on:

- opening the current file's PDF in **Zathura**
- forward-searching from the current cursor position with **SyncTeX**
- optionally auto-opening or auto-syncing after successful builds

## What "PDF sync" actually means

Think of PDF sync as:

> "my cursor is here in the `.tex` file, so open the PDF at the matching place"

So yes - if your cursor is sitting on a paragraph or equation in txtr and you run:

```text
:pdf
```

txtr asks Zathura to jump the PDF to the spot that came from that source location. Pretty cool fr.

That flow is usually called **forward search** :

- **source** (`.tex` in txtr) -> **PDF** (Zathura)

` :pdf open ` is a little different:

- it just opens the PDF
- it does **not** try to jump to your current cursor location

` :pdf ` and ` :pdf sync ` are the commands that do the jump.

## Enable the plugin

```toml
[plugins]
enabled = ["zathura"]
```

Restart txtr after enabling it.

## Commands

| Command | Description |
|---|---|
| `:pdf` | forward-search the current cursor position in Zathura |
| `:pdf sync` | same as `:pdf` |
| `:pdf open` | open the current file's PDF in Zathura |
| `:pdf close` | close the Zathura window launched by txtr |

` :pdf close ` only tracks the Zathura window txtr launched itself.

## Config

```toml
[zathura]
executable = "zathura"
extra_args = []
auto_open_on_build = false
auto_sync_on_build = false
```

- `executable` lets you point at a custom Zathura binary
- `extra_args` appends extra CLI flags before the PDF path
- `auto_open_on_build` opens the PDF after a successful build if txtr is not already tracking a Zathura window
- `auto_sync_on_build` runs SyncTeX forward search after a successful build

If both auto options are `true`, txtr prefers the sync flow.

## Notes

- you need Zathura installed on your system - if you don't, what are you doing with your life
- build the file at least once so the PDF exists
- SyncTeX needs a `.synctex.gz` file; txtr's built-in compiler presets generate it for the supported engines
- if you use `compiler.custom_cmd`, include your own SyncTeX flag or `:pdf sync` will warn that no SyncTeX data exists
