--- 
title: Snippets Overview
description: How the txtr snippet engine works
--- 

txtr ships with a LaTeX snippet library and a simple engine for expanding them. Snippets are defined in`~/.config/txtr/snippets.toml` and can be edited freely - the file is yours to customize.

## Trigger types

There are two ways that a snippet in txtr can fire.

### Auto-expand

The snippet fires as you type, the moment the trigger sequence is completed. No extra keypress is needed.
