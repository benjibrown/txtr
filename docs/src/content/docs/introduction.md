---
title: Introduction
description: What txtr is and why it exists.
---


txtr is a Vim-style LaTeX editor that runs entirely in the terminal. It is built in Python on top of [Textual](https://textual.textualize.io/), and is designed for one thing: writing LaTeX fast. 

Most LaTeX editors are either heavyweight GUI applications or plain text editors bolted onto a terminal. txtr sits in the middle - a purpose-built TUI that understands LaTeX structure, provides a rich snippet engine, and gets out of your way so you can focus on writing. 

Of course, snippet engines can be installed to many editors, but txtr's has them built in and optimized for LaTeX - zero configuration required to get up and running. It also has baked-in support for compiling your document, parsing errors and uses the keybinds you already know and love.

## Why txtr?

- **Vim Keybinds.** Normal, Insert, Visual, Command and Search modes. If you use Vim, you know how to use txtr. If you don't, we have plenty of documentation to get you going.
- **Snippet engine.** Auto-expand triggers for greek letters, fractions, environemnts and more. Tab stops let you fill in the blanks and keep your hands on the keyboard. Plenty built in, plenty of room for your own.
- **LaTeX autocomplete.** Start typing `\` and a popup offers matching commands.
- **Auto Pairs.** Automatically insert closing braces, brackets, parentheses and quotes. Skip over them when you type the closing character. 
- **Themes** - Ships with Catppuccin Mocha and Gruvbox Dark. Custom themes easily configured with a simple TOML file. 
- **Compilitation.** Compile your document without even leaving the editor. Baked-in support for `pdflatex`, `xelatex`, `lualatex`, `latexmk` and `tectonic`. Custom compilation commands also supported. Parse errors and jump straight to the offending line.


## Status

txtr is under active development. Core editing is stable. Features are still being actively built, refined and documented. Look out for a plugin system in the future, spell checking, more themes and citation management.

Contributions always welcome - check out the [repo](https://github.com/benjibrown/txtr)
