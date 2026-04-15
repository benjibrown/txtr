--- 
title: Snippets Overview
description: How the txtr snippet engine works
--- 

txtr ships with a bundled LaTeX snippet library and a simple snippet engine for expanding them quickly while you type. Your editable snippet file lives at `~/.config/txtr/snippets.toml`.

## Trigger types

There are two ways that a snippet in txtr can fire.

### Auto-expand

The snippet fires as you type, the moment the trigger sequence is completed. No extra keypress is needed.

Auto-expand is used for symbol sequences that are unambiguous in a LaTeX document, such as:

- `//` -> `\frac{...}{...}`
- `@a` -> `\alpha`
- `!=` -> `\neq`
- `...` -> `\ldots`

If an auto-expand fires unexpectedly, press `Backspace` to undo the expansion.

### Tab-triggered

Type the trigger word, then press `Tab`.

Tab-triggered snippets are used for alphabetic triggers like `int`, `sum`, `cite`, `ref`, `lab`, or environment shorthands like `ali`, `eq`, and `itm`. These would be too noisy if they expanded automatically.

## Tab Stops

Most snippets include tab stops: `${1}`, `${2}`, and so on.

After a snippet expands:

1. your cursor lands on the first tab stop
2. pressing `Tab` jumps to the next stop
3. pressing `Shift+Tab` clears the remaining stops and exits snippet navigation

Tab stops also allow placeholder text. A stop like `${1:title}` expands with `title` already filled in, which you can overwrite or skip past with `Tab`.

## Undo and false positives

Auto-expanding snippets checkpoint the buffer before they fire. That means if `//` or `@a` expands at the wrong time, one `Backspace` reverts the expansion cleanly.

This is why txtr keeps auto-expansion mostly for symbolic triggers and leaves word-like triggers for `Tab`.

## Writing workflow examples

### Fast math input

1. type `//`
2. txtr expands it to `\frac{${1}}{${2}}`
3. type the numerator
4. press `Tab`
5. type the denominator

### Citation and reference flow

1. type `cite`
2. press `Tab`
3. txtr inserts `\cite{${1}}`
4. type inside the braces and citation autocomplete takes over

The same pattern works for `ref`, `eref`, and `lab`.

## Customisation

### Snippet file location

``` ```
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
- `body` - the expansion text
- `auto_expand` - `true` for auto-expand, `false` for tab-triggered expansion

The above snippet will expand `ms` to `\mycommand{}` when you press `Tab` after typing `ms`. The cursor will be placed inside the braces, ready for you to type whatever your heart desires.

## Bundled defaults

txtr already ships with:

- greek-letter shortcuts
- common math relation shortcuts
- environment snippets
- document templates
- common LaTeX commands like `int`, `sum`, `lim`, `cite`, `ref`, and `label`

See [Snippet Reference](/snippets/reference) for a fuller grouped list.
