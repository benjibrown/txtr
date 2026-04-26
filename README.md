<div align="center">

<img src="https://txtr.benji.mom/_astro/logo.D7KM1bTr_Z1HYzg2.svg" alt="txtr screenshot" width="360"/>

**A Vim-style LaTeX editor for the terminal.**


<img src="https://txtr.benji.mom/ss.png" alt="txtr screenshot" width="800"/>

<a href="https://txtr.benji.mom"><strong>Read the docs</strong></a> | <a href="https://pypi.org/project/texitor/">PyPI</a>
</div>

---

txtr (aka texitor) is a terminal LaTeX editor built for speed. It mixes Vim-style modal editing with snippets, autocomplete, citations, compiler tooling, and plugins in one clean TUI.

> Under active development. Expect bugs :)

## Docs

**The full docs are here: [txtr.benji.mom](https://txtr.benji.mom)**

If you only read one extra thing after this README, make it one of these:

- [installation](https://txtr.benji.mom/installation)
- [quick start](https://txtr.benji.mom/quickstart)
- [snippets overview](https://txtr.benji.mom/snippets/overview)
- [config overview](https://txtr.benji.mom/config/overview)

## Installation

```bash
pip install texitor
```

If your system complains about installing packages globally, use `pipx`, `uv`, or a virtual environment instead.

```bash
pipx install texitor
```

```bash
uv tool install texitor
```

```bash
python -m venv txtr-env
source txtr-env/bin/activate
pip install texitor
```

Requires Python 3.11 or later. More install details live in the docs: [txtr.benji.mom/installation](https://txtr.benji.mom/installation)

## What even is LaTeX?

LaTeX is a typesetting system used a lot for maths, science, essays, notes, and papers. It is great once you know it, but it can be pretty slow and bracket-heavy to write by hand.

That is the whole point of txtr: make writing LaTeX in the terminal feel fast instead of annoying.

## Quick start

```bash
txtr file.tex
```

If the file does not exist, txtr creates it. On first run txtr seeds config, snippets, commands, and keybind overrides into `~/.config/txtr/`.

Never used a Vim-style editor before? This is the tiny version:

- `i` enters Insert mode so you can type (this is how you can actually get text into the editor)
- `Esc` takes you back to Normal mode
- `:w` saves
- `:q` quits
- `:wq` saves and quits
- `?` opens the help menu

Once you are inside txtr:

- `:` opens command mode
- `:snippets` jumps straight to snippet help
- `:config show` opens the config panel
- `:plugin list` shows installed plugins
- typing `\fra` opens LaTeX autocomplete
- `Up` / `Down` moves through autocomplete and `Enter` or `Ctrl+Space` accepts it
- typing a snippet trigger like `//` or `doc` expands it fast (`doc` still needs `Tab`)

txtr also remembers where you were in a file when you reopen it by default, so hopping back into longer docs feels way nicer.

If you want the fuller walkthrough, go straight to **[the quick start docs](https://txtr.benji.mom/quickstart)**.

## What ships with txtr

- Vim-style modal editing for `.tex` files
- LaTeX snippets and completions
- citation autocomplete from `.bib` files
- compiler commands, buildwatch, and PDF build workflows
- file explorer, recents, and multi-buffer workflow
- restore cursor position when reopening files
- built-in plugins:
  - `wordcount` - latex-aware word count
  - `freeze` - screenshot/export via the freeze CLI
  - `zathura` - external PDF open + SyncTeX forward search
- installable user plugins on top of the built-ins
- a full docs site with config, snippets, themes, and plugin guides

Built-in plugins ship with txtr, but they are still configured and enabled like normal plugins.

## Docs, again because they matter

The README is only the short version. The proper setup/config/snippet/plugin guides live at:

**[https://txtr.benji.mom](https://txtr.benji.mom)**

## Notes

- requires Python 3.11+
- compiler features expect tools like `latexmk` or `pdflatex` to be installed
- system clipboard features rely on platform clipboard tools
- some plugins rely on external tools too, for example `freeze` and `zathura`

## Compatibility 
- Linux - fully supported and tested 
- MacOS - supported but not thoroughly tested 
- Windows - not currently supported, but WSL should work fine - txtr will run but do expect errors 
> If you would like to port txtr to Windows, please open an issue or PR on GitHub. I don't have access to a Windows machine but would be happy to review and merge contributions that add support.

## Contributing

txtr is early-stage. If you find a bug or want to add something, open an issue or PR on [GitHub](https://github.com/benjibrown/txtr). 
> tl;dr - just make a pr ...
