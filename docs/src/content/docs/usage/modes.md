---
title: Modes
description: txtr's modal editing system.
---

txtr is modal. Every keypress means something different depending on the active mode. The current mode is always shown in the statusbar pill on the left.

## Normal mode

The default mode. Used for navigation, deletion, yanking, and entering other modes. You cannot type text directly in Normal mode.

Enter with `Escape` or `Ctrl+[` from any other mode.

## Insert mode

Text entry. Every printable character is inserted at the cursor. Snippets fire here. Autocomplete appears as you type `\commands`.

| Key | Action |
|---|---|
| `i` | Enter before cursor |
| `I` | Enter at line start |
| `a` | Enter after cursor |
| `A` | Enter at line end |
| `o` | Open new line below and enter |
| `O` | Open new line above and enter |

## Visual mode

Character-wise selection. Move the cursor to extend the selection.

Press `v` from Normal mode.

## Visual Line mode

Line-wise selection. Entire lines are selected as you move up and down.

Press `V` from Normal mode.

## Command mode

Type `:` commands. Press `:` from Normal mode, type a command, press `Enter` to execute.

The statusbar input turns red and shows `COMMAND`. Press `Escape` to cancel.

Help and config popups stay open while in Command mode — you can read them while typing commands.

## Search mode

Forward search. Press `/` from Normal mode, type a pattern, press `Enter`.

Press `n` / `N` in Normal mode to jump between matches. Matches are highlighted in the editor.
