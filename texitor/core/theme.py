# I LOVE THEMES 
# im gonna comment this loads so it is actually maintainable for once
# theme system - defines color palettes for the editor
# built-in: catppuccin (default), gruvbox
# custom: set name = "custom" in config and provide custom_path pointing to a toml file
#
# custom theme toml format (flat):
#   name = "my-theme"
#   bg = "#1a1b26"
#   bg_alt = "#16161e"
#   ... (all fields required, see Theme dataclass below)

from __future__ import annotations

import re
from dataclasses import dataclass, fields

_HEX_RE = re.compile(r'^#[0-9a-fA-F]{6}$')

# stores a warning message if theme loading had issues - checked by app on mount
_startup_warning: str | None = None


@dataclass
class Theme:
    name: str
    # backgrounds
    bg: str           # main editor background
    bg_alt: str       # darker bg (statusbar, panel headers)
    bg_popup: str     # popup and dropdown surface
    cursor_line: str  # current line subtle highlight
    bg_sel: str       # visual selection background
    bg_search: str    # search match highlight background
    # borders and separators
    border: str
    # foregrounds
    fg: str           # default text
    fg_dim: str       # very muted (disabled, placeholder)
    fg_muted: str     # muted (line numbers, comments)
    fg_sub: str       # subtle secondary text
    # semantic accent colors
    accent: str       # primary - normal mode, keybinds, search prompt
    accent2: str      # secondary - visual mode, section headers
    green: str        # insert mode cursor, LaTeX env names
    yellow: str       # warnings
    orange: str       # math regions
    red: str          # errors, command mode


BUILTIN_THEMES: dict[str, Theme] = {
    "catppuccin": Theme(
        name="catppuccin",
        bg="#1e1e2e",
        bg_alt="#181825",
        bg_popup="#313244",
        cursor_line="#252537",
        bg_sel="#45475a",
        bg_search="#f9e2af",
        border="#45475a",
        fg="#cdd6f4",
        fg_dim="#6c7086",
        fg_muted="#585b70",
        fg_sub="#a6adc8",
        accent="#89b4fa",
        accent2="#cba6f7",
        green="#a6e3a1",
        yellow="#f9e2af",
        orange="#fab387",
        red="#f38ba8",
    ),
    "gruvbox": Theme(
        name="gruvbox",
        bg="#282828",
        bg_alt="#1d2021",
        bg_popup="#3c3836",
        cursor_line="#32302f",
        bg_sel="#504945",
        bg_search="#fabd2f",
        border="#504945",
        fg="#ebdbb2",
        fg_dim="#7c6f64",
        fg_muted="#928374",
        fg_sub="#a89984",
        accent="#83a598",
        accent2="#d3869b",
        green="#b8bb26",
        yellow="#fabd2f",
        orange="#fe8019",
        red="#fb4934",
    ),
}


def validate(t: Theme) -> list[str]:
    # returns list of "field=value" strings for any invalid hex colors
    bad = []
    for f in fields(t):
        if f.name == "name":
            continue
        val = getattr(t, f.name)
        if not isinstance(val, str) or not _HEX_RE.match(val):
            bad.append(f"{f.name}={val!r}")
    return bad


def _loadCustomTheme(path: str) -> Theme:
    # loads a theme from a toml file - raises on any error
    import tomllib

    with open(path, "rb") as fh:
        data = tomllib.load(fh)

    # accept flat format or optional [colors] nesting
    colors = data.get("colors", data)
    name = str(data.get("name", "custom"))

    known = {f.name for f in fields(Theme)} - {"name"}
    missing = known - set(colors.keys())
    if missing:
        raise ValueError(f"missing fields: {', '.join(sorted(missing))}")

    return Theme(name=name, **{k: str(colors[k]) for k in known})


def loadTheme() -> Theme:
    # loads theme from config - falls back to catppuccin on any failure
    # stores a startup warning if something went wrong
    global _startup_warning
    _startup_warning = None

    try:
        from texitor.core.config import config as cfg
        cfg.load()  # ensure user config is read from disk before checking theme
        name = cfg.get("theme", "name", "catppuccin")
    except Exception:
        name = "catppuccin"

    if name == "custom":
        try:
            from texitor.core.config import config as cfg
            path = cfg.get("theme", "custom_path", "")
        except Exception:
            path = ""

        if not path:
            _startup_warning = "custom theme selected but no custom_path set -- using catppuccin"
            return BUILTIN_THEMES["catppuccin"]

        try:
            t = _loadCustomTheme(path)
            errs = validate(t)
            if errs:
                preview = ", ".join(errs[:2]) + ("..." if len(errs) > 2 else "")
                _startup_warning = f"custom theme has invalid colors ({preview}) -- using catppuccin"
                return BUILTIN_THEMES["catppuccin"]
            return t
        except Exception as e:
            _startup_warning = f"failed to load custom theme: {e} -- using catppuccin"
            return BUILTIN_THEMES["catppuccin"]

    if name not in BUILTIN_THEMES:
        _startup_warning = f'unknown theme "{name}" -- using catppuccin'
        return BUILTIN_THEMES["catppuccin"]

    return BUILTIN_THEMES[name]


def getStartupWarning() -> str | None:
    return _startup_warning


# loaded once at import time - all UI modules reference this
theme = loadTheme()

