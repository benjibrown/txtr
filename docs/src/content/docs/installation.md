--- 

title: Installation 
description: How to install txtr. 
--- 

## Requirements

- Python 3.10 or higher 
- A terminal with 256-colour support (essentially any modern terminal) 
- `pip` for installing the package and its dependencies 

## Installation 

There are two main ways to install txtr: using `pip` or installing from source. The recommended method is to use `pip` - this pulls the latest stable version from PyPI and handles dependencies automatically. Installing from source will give you the latest development version which may not be entirely stable but will have the latest features and bug fixes.

### Install from PyPI 

```
pip install texitor
```
> The package name on PyPI is `texitor`. The command you run to use the editor is `txtr`.

Some operating systems may throw an error about installing system-wide packages with pip. If this is the case then use `pipx` instead or install txtr in a virtual environment. 

```
pipx install texitor
```
**or**

```python
python -m venv txtr-env
source txtr-env/bin/activate  
pip install texitor
```

### Install from Source 

```
git clone https://github.com/benjibrown/txtr.git 
cd txtr 
pip install -e .
```

## First run 

On first launch, txtr seeds your config directory with the necessary files:
```
~/.config/txtr/ 
    config.toml     # editor preferences 
    snippets.toml   # snippet library (fully customizable)
    commands.toml   # command definitions (for autocomplete popup)
```
These files are only created once. Deleting them will regenerate the defaults on the next launch. You can edit these files to customize the editor's behavior, add snippets, and define commands.

Two very useful first-run notes:

- `snippets.toml` powers snippet expansion
- `commands.toml` powers the LaTeX autocomplete popup

txtr now merges your local files on top of the bundled defaults, so keeping an older customised file no longer means you miss newer built-in snippet/completion additions.



## System clipboard (optional)

In order for txtr to access your system clipboard (`system_clipboard = true` in config), you need one of the following clipboard utilities installed:
| Platform | Tool |
| --- | --- |
| macOS | `pbcopy`/`pbpaste` (pre-installed) |
| Wayland | `wl-clipboard`|
| X11 | `xclip` or `xsel` |

Without any of these, txtr falls back to its internal yank register.


## LaTeX Compilation (optional) 

Whilst this section is technically optional, this is one of the main use cases for txtr. If you want compile LaTeX documents directly from your editor, you will require a TeX distribution installed on your system and a CLI LaTeX compiler. I recommend choosing one of the following (all have built-in support in txtr):
- `latexmk` (recommended)
- `pdflatex`
- `xelatex` 
- `lualatex`
- `tectonic` 


txtr also supports custom compilation commands, so if you have a preferred compiler that isn't supported by default, you can configure a compilation command in `config.toml` and continue with your workflow as normal!
