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

Requires Python 3.11 or later.

## Usage

```
txtr file.tex
```

If the file does not exist, txtr creates it. Config and snippets are seeded to `~/.config/txtr/` on first run.

## Whats in txtr ???

- Vim-style modal editing for `.tex` files
- LaTeX snippets and completions
- citation autocomplete from `.bib` files
- compiler commands and build/watch flows
- built-in + installable plugins
- a full docs site with config, snippets, and plugin guides

## Quick start

```bash
txtr file.tex
```

Config and snippets are seeded into `~/.config/txtr/` on first run.

Inside txtr:

- `?` opens the help menu
- `:` opens command mode
- `:snippets` jumps straight to snippet help
- `:config show` opens the config panel
- `:plugin list` shows installed plugins

**[IF YOU GET STUCK, READ THE DOCS! (click me)](https://txtr.benji.mom)**

## Documentation

The full docs live at **[txtr.benji.mom](https://txtr.benji.mom)**.

Useful starting points:

- snippets: [txtr.benji.mom/snippets/overview](https://txtr.benji.mom/snippets/overview)
- configuration: [txtr.benji.mom/config/overview](https://txtr.benji.mom/config/overview)
- plugins: [txtr.benji.mom/plugins/overview](https://txtr.benji.mom/plugins/overview)
- plugin development: [txtr.benji.mom/plugins/development](https://txtr.benji.mom/plugins/development)

## Notes

- requires Python 3.11+
- compiler features expect tools like `latexmk` or `pdflatex` to be installed
- system clipboard features rely on platform clipboard tools

## Contributing

txtr is early-stage. If you find a bug or want to add something, open an issue or PR on [GitHub](https://github.com/benjibrown/txtr). 
> tl;dr - just make a pr ...



