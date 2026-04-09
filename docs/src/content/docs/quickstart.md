--- 
title: Quick Start 
description: Open a file and start writing LaTeX.
--- 

## Open a file 

```
txtr first.tex
```
This will open the file `first.tex` in txtr (your new favorite editor). If the file does not exist, it will be created.
> You can also run `txtr` without any arguments to open the editor without a file currently active, instead you will see the splash screen and recently opened files.

## Write something

When you first open the editor, you are in `NORMAL` mode. This is where you can undo, redo, save and navigate the file.

To start writing, press `i` to enter `INSERT` mode. The statusbar will now show `INSERT`.

From here, you can type anything you would like. Want to leave `INSERT` mode? Press `ESC` to return to `NORMAL` mode.

Type a backslash `\` when in insert mode - an autocomplete popup will appear. Keep typing to narrow down the option, hit enter when you see the one you want or hit tab to cycle through the options.

## Use your first snippet 

In `INSERT` mode, type `//` - this auto-expands to `\frac{}{}` and places your cursor in the first set of curly braces. Hit `Tab` to jump to the next set.

Type `@a` - it auto-expands to `\alpha`.

For tab-triggered snippets, type `int` (for integral) and press `Tab` - it expands to `\int_{}^{} ` and places your cursor in the first set of `{}`. Hit tab to jump to the next set.

Type `doc` and hit `Tab` - it expands to a full document template. Getting you started with a new document has never been easier!

Check out the next section on how to see all the available snippets!

## Save and quit 

From Normal mode:
```
:w      save 
:q      quit 
:wq     save and quit 
:q!     quit without saving
```
> Note that `:` is used to enter command mode, `w`, `q` and `!` are the commands themselves. 

## Open the help menu 

Press `?` in Normal mode to open the help menu or run `:help` in command mode. The help menu has 3 key tabs:
- **Keybinds** - shows all the keybinds available in the editor. 
- **Snippets** - shows all the snippets available in the editor. 
- **Commands** - shows all the commands available in command mode.
- **[WIP] Plugins** - shows all the commands available for plugins.

Press `Tab` to cycle through the tabs and `ESC` or `q` to close. 

There are plenty of snippets to explore and you can even create your own. Give the snippets menu a look and see what you can find!
> Pro tip: typing `:snips` or `:snippets` will open the help menu directly on the snippets tab.
