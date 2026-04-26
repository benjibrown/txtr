<div align="center">

<img src="https://txtr.benji.mom/_astro/logo.D7KM1bTr_Z1HYzg2.svg" alt="txtr screenshot" width="360"/>

**A Vim-style LaTeX editor for the terminal.**


<!-- screenshot -->
<img src="https://txtr.benji.mom/ss.png" alt="txtr screenshot" width="800"/>

<a href="https://txtr.benji.mom">Documentation</a> | <a href="https://pypi.org/project/texitor/">PyPI</a>
</div>

---

txtr (aka texitor) is a terminal-based LaTeX editor built for speed. It combines Vim-style modal editing with snippets, completions, citations, compiler tooling, and a growing plugin system.

> Under active development. Expect bugs :)

## Installation

```
pip install texitor
```
> In-depth installation instructions are in the docs - see [txtr.benji.mom/installation](https://txtr.benji.mom/installation) for more details.

If you encouter an error regarding installing system wide packages, you may need to install with `pipx` or in a virtual environment. 

Requires Python 3.11 or later.

## Quick start

```bash
txtr file.tex
```

If the file does not exist, txtr creates it. On first run txtr seeds config, snippets, commands, and keybind overrides into `~/.config/txtr/`.

Never used a Vim-style editor before? The bare minimum to get going is:

- `i` enters Insert mode so you can type (this is how you can actually get text into the editor)
- `Esc` takes you back to Normal mode
- `:w` saves
- `:q` quits
- `:wq` saves and quits
- `?` opens the help menu

Inside txtr:

- `:` opens command mode
- `:snippets` jumps straight to snippet help
- `:config show` opens the config panel
- `:plugin list` shows installed plugins
- `Up` / `Down` moves through autocomplete and `Enter` or `Ctrl+Space` accepts it
- typing a snippet trigger like `//` or `doc` expands it fast (`doc` still needs `Tab`)


## What even is LaTeX?

LaTeX is a typesetting system commonly used for academic writing, especially in fields like mathematics and physics. It allows you to write documents with complex formatting and is particularly good at handling equations, citations and references. 

LaTeX is generaly quite long-winded to write by hand, which is exactly why txtr exists - to make LaTeX editing faster, more efficient and collate together all the utilities you may want into one single editor.

## What ships with txtr

- Vim-style modal editing for `.tex` files
- LaTeX snippets and completions
- citation autocomplete from `.bib` files
- compiler commands, buildwatch, and PDF build workflows
- built-in plugins:
  - `wordcount` - latex-aware word count
  - `freeze` - screenshot/export via the freeze CLI
  - `zathura` - external PDF open + SyncTeX forward search
- installable user plugins on top of the built-ins
- a full docs site with config, snippets, themes, and plugin guides

Built-in plugins ship with txtr, but they are still configured and enabled like normal plugins. The README is just the quick overview - the docs are the proper source of truth for setup and config.

**[IF YOU GET STUCK, READ THE DOCS! (click me)](https://txtr.benji.mom)**

## Documentation

The full docs live at **[txtr.benji.mom](https://txtr.benji.mom)**.

Useful starting points:

- snippets: [txtr.benji.mom/snippets/overview](https://txtr.benji.mom/snippets/overview)
- configuration: [txtr.benji.mom/config/overview](https://txtr.benji.mom/config/overview)
- plugins: [txtr.benji.mom/plugins/overview](https://txtr.benji.mom/plugins/overview)
- zathura pdf sync: [txtr.benji.mom/plugins/zathura](https://txtr.benji.mom/plugins/zathura)
- plugin development: [txtr.benji.mom/plugins/development](https://txtr.benji.mom/plugins/development)

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
