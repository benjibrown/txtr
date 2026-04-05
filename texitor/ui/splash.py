# splash screen / landing page - shown when txtr opens with no file argument
# nvim-style: rotating logo, tagline, version, recent files list
# j/k navigate recents, enter opens selected, any other key dismisses

from __future__ import annotations
import random
from typing import TYPE_CHECKING

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

from texitor.core.theme import theme as _t
import texitor.core.recents as _recents

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

_ACCENT  = Style(color=_t.accent, bold=True)
_DIM     = Style(color=_t.fg_dim)
_SUB     = Style(color=_t.fg_sub)
_SEC     = Style(color=_t.accent2, bold=True)
_FG_SEL  = Style(color=_t.fg, bgcolor=_t.bg_sel, bold=True)
_ACC_SEL = Style(color=_t.accent, bgcolor=_t.bg_sel, bold=True)

_LOGO_A = []
    "  █████                 █████             ",
    " ░░███                 ░░███              ",
    " ███████   █████ █████ ███████   ████████ ",
    "░░░███░   ░░███ ░░███ ░░░███░   ░░███░░███",
    "  ░███     ░░░█████░    ░███     ░███ ░░░ ",
    "  ░███ ███  ███░░░███   ░███ ███ ░███     ",
    "  ░░█████  █████ █████  ░░█████  █████    ",
    "   ░░░░░  ░░░░░ ░░░░░    ░░░░░  ░░░░░    ",
]

_LOGO_B = []
    " _            _      ",
    "| |___  __  _| |_ _ _",
    "| __\\ \\/ /| | __| '_|",
    "|_|  >  < |_|\\__|_|  ",
    "   /_/\\_\\             ",
]

_LOGO_C = []
    "                                                                                    ",
    "                                                                                    ",
    "         tttt                                      tttt                             ",
    "      ttt:::t                                   ttt:::t                             ",
    "      t:::::t                                   t:::::t                             ",
    "      t:::::t                                   t:::::t                             ",
    "ttttttt:::::ttttttt   xxxxxxx      xxxxxxxttttttt:::::ttttttt   rrrrr   rrrrrrrrr   ",
    "t:::::::::::::::::t    x:::::x    x:::::x t:::::::::::::::::t   r::::rrr:::::::::r  ",
    "t:::::::::::::::::t     x:::::x  x:::::x  t:::::::::::::::::t   r:::::::::::::::::r ",
    "tttttt:::::::tttttt      x:::::xx:::::x   tttttt:::::::tttttt   rr::::::rrrrr::::::r",
    "      t:::::t             x::::::::::x          t:::::t          r:::::r     r:::::r",
    "      t:::::t              x::::::::x           t:::::t          r:::::r     rrrrrrr",
    "      t:::::t              x::::::::x           t:::::t          r:::::r            ",
    "      t:::::t    tttttt   x::::::::::x          t:::::t    ttttttr:::::r            ",
    "      t::::::tttt:::::t  x:::::xx:::::x         t::::::tttt:::::tr:::::r            ",
    "      tt::::::::::::::t x:::::x  x:::::x        tt::::::::::::::tr:::::r            ",
    "        tt:::::::::::ttx:::::x    x:::::x         tt:::::::::::ttr:::::r            ",
    "          ttttttttttt xxxxxxx      xxxxxxx          ttttttttttt  rrrrrrr            ",
    "                                                                                    ",
]

_LOGO_D = []
    "     s                      s                 ",
    "    :8                     :8                 ",
    "   .88       uL   ..      .88       .u    .   ",
    "  :888ooo  .@88b  @88R   :888ooo  .d88B :@8c  ",
    "-*8888888 '\"Y888k/\"*P  -*8888888 =\"8888f8888r ",
    "  8888       Y888L       8888      4888>'88\"  ",
    "  8888        8888       8888      4888> '    ",
    "  8888        `888N      8888      4888>      ",
    " .8888Lu=  .u./\"888&    .8888Lu=  .d888L .+   ",
    " ^%888*   d888\" Y888*\"  ^%888*    ^\"8888*\"    ",
    "   'Y\"    ` \"Y   Y\"       'Y\"        \"Y\"      ",
]
_LOGOS = [_LOGO_A, _LOGO_B, _LOGO_C, _LOGO_D]
_VERSION = "v1.9.8"
_TAGLINE = "LaTeX, fast."

_TICKER_ITEMS = []
    r"\frac{a}{b}",
    r"\int_0^\infty f(x)\,dx",
    r"\alpha + \beta = \gamma",
    r"\begin{align}",
    r"\nabla \cdot \mathbf{E} = \rho",
    r"\sum_{n=1}^{N} a_n",
    r"\forall x \in \mathbb{R}",
    r"\mathcal{L}(x, \lambda)",
    r"\partial_t u = \Delta u",
    r"\lim_{x \to 0} \frac{\sin x}{x}",
    r"\binom{n}{k} = \frac{n!}{k!(n-k)!}",
    r"\hat{H}\psi = E\psi",
    r"\text{s.t. } Ax \leq b",
    r"\oint_C \mathbf{F} \cdot d\mathbf{r}",
    r"\mathbb{P}(A \mid B)",
    r"\varepsilon \to 0^+",
]
# build a long looping plain string and a parallel list of styles per char
_SEP = "     ·     "

def _build_ticker():
    plain = (_SEP.join(_TICKER_ITEMS) + _SEP) * 3
    return plain

_TICKER_PLAIN = _build_ticker()
_TICKER_LEN = len(_TICKER_PLAIN) // 3  # one full cycle length

_HINTS = []
    ("j/k", "navigate"),
    ("enter", "open"),
    ("e", "new file"),
    (":e", "open file"),
    ("q", "quit"),
]


